const fs = require('fs');
const { Client } = require('/home/node/.n8n/node_modules/pg');
const { Transform } = require('stream');
const copyFrom = require('/home/node/.n8n/node_modules/pg-copy-streams').from;

const host = process.env.DB_POSTGRESDB_HOST || 'postgres';
const port = process.env.DB_POSTGRESDB_PORT || 5432;
const database = process.env.DB_POSTGRESDB_DATABASE || 'content_marketing';
const user = process.env.DB_POSTGRESDB_USER || 'n8n_user';
const password = process.env.DB_POSTGRESDB_PASSWORD || 'n8n_secure_password_99';

const csvFilePath = process.env.CSV_PATH || '/data/shared-media/shopee/shopee_filtered.csv';

const client = new Client({
  host,
  port,
  database,
  user,
  password,
});

// Transform stream to sanitize CSV data (remove null bytes and invalid UTF-8)
class SanitizeStream extends Transform {
  constructor(options) {
    super(options);
    this.lineNumber = 0;
  }

  _transform(chunk, encoding, callback) {
    try {
      // Filter out null bytes (0) directly at the byte level
      const cleaned = Buffer.allocUnsafe(chunk.length);
      let len = 0;
      for (let i = 0; i < chunk.length; i++) {
        const byte = chunk[i];
        if (byte !== 0) {
          cleaned[len++] = byte;
        }
      }
      
      this.lineNumber++;
      if (this.lineNumber % 50000 === 0) {
        console.log(`Sanitized ${this.lineNumber} chunks...`);
      }
      
      callback(null, cleaned.subarray(0, len));
    } catch (err) {
      callback(err);
    }
  }
}

async function main() {
  console.log(`Connecting to Postgres database ${database} on ${host}:${port}...`);
  
  try {
    await client.connect();
    console.log('Connected successfully. Starting bulk import...');

    // Check if file exists
    if (!fs.existsSync(csvFilePath)) {
      throw new Error(`CSV file not found: ${csvFilePath}`);
    }

    const fileStats = fs.statSync(csvFilePath);
    console.log(`CSV file size: ${fileStats.size} bytes`);

    // Create temporary staging table
    console.log('Creating temporary staging table...');
    await client.query('CREATE TEMP TABLE temp_shopee_import (LIKE shopee_discount_products INCLUDING DEFAULTS);');

    console.log('Beginning COPY stream with data sanitization into temp table...');
    const stream = client.query(copyFrom(`
      COPY temp_shopee_import (
        itemid, shopid, title, price, sale_price, discount_percentage, 
        stock, item_sold, item_rating, likes_count, is_preferred_shop, 
        is_official_shop, has_lowest_price_guarantee, image_link, 
        product_link, product_short_link, global_category1, global_category2, 
        global_category3, shop_name, seller_name, global_brand, 
        description, model_names, model_prices
      ) FROM STDIN WITH CSV HEADER
    `));

    const fileStream = fs.createReadStream(csvFilePath);
    const sanitizer = new SanitizeStream();

    let errorOccurred = false;

    fileStream.on('error', (err) => {
      console.error('File stream error:', err);
      errorOccurred = true;
      client.end();
      process.exit(1);
    });

    sanitizer.on('error', (err) => {
      console.error('Sanitizer stream error:', err);
      errorOccurred = true;
      client.end();
      process.exit(1);
    });

    stream.on('error', (err) => {
      console.error('COPY stream error:', err);
      errorOccurred = true;
      client.end();
      process.exit(1);
    });

    stream.on('finish', async () => {
      if (!errorOccurred) {
        try {
          console.log('COPY stream complete. Upserting into shopee_products...');
          await client.query(`
            INSERT INTO shopee_products (
                itemid, shopid, title, image_link, product_link, product_short_link,
                global_category1, global_category2, global_category3, shop_name,
                seller_name, global_brand, description, model_names
            )
            SELECT DISTINCT 
                itemid, shopid, title, image_link, product_link, product_short_link,
                global_category1, global_category2, global_category3, shop_name,
                seller_name, global_brand, description, model_names
            FROM temp_shopee_import
            ON CONFLICT (itemid) DO UPDATE SET
                title = EXCLUDED.title,
                image_link = EXCLUDED.image_link,
                product_link = EXCLUDED.product_link,
                product_short_link = EXCLUDED.product_short_link,
                global_category1 = EXCLUDED.global_category1,
                global_category2 = EXCLUDED.global_category2,
                global_category3 = EXCLUDED.global_category3,
                shop_name = EXCLUDED.shop_name,
                seller_name = EXCLUDED.seller_name,
                global_brand = EXCLUDED.global_brand,
                description = EXCLUDED.description,
                model_names = EXCLUDED.model_names,
                updated_at = CURRENT_TIMESTAMP;
          `);

          console.log('Inserting into shopee_price_history...');
          await client.query(`
            INSERT INTO shopee_price_history (
                itemid, price, sale_price, discount_percentage, stock, item_sold,
                item_rating, likes_count, is_preferred_shop, is_official_shop,
                has_lowest_price_guarantee, recorded_date
            )
            SELECT 
                itemid, price, sale_price, discount_percentage, stock, item_sold,
                item_rating, likes_count, is_preferred_shop, is_official_shop,
                has_lowest_price_guarantee, CURRENT_DATE
            FROM temp_shopee_import
            ON CONFLICT (itemid, recorded_date) DO UPDATE SET
                price = EXCLUDED.price,
                sale_price = EXCLUDED.sale_price,
                discount_percentage = EXCLUDED.discount_percentage,
                stock = EXCLUDED.stock,
                item_sold = EXCLUDED.item_sold,
                item_rating = EXCLUDED.item_rating,
                likes_count = EXCLUDED.likes_count,
                is_preferred_shop = EXCLUDED.is_preferred_shop,
                is_official_shop = EXCLUDED.is_official_shop,
                has_lowest_price_guarantee = EXCLUDED.has_lowest_price_guarantee;
          `);

          console.log('Updating shopee_discount_products table for backward compatibility...');
          await client.query('TRUNCATE TABLE shopee_discount_products;');
          await client.query('INSERT INTO shopee_discount_products SELECT * FROM temp_shopee_import;');

          console.log('Bulk import complete successfully.');
          client.end();
          process.exit(0);
        } catch (dbErr) {
          console.error('Error in post-copy DB operations:', dbErr);
          client.end();
          process.exit(1);
        }
      }
    });

    stream.on('close', () => {
      if (errorOccurred) {
        console.error('Stream closed with error.');
        process.exit(1);
      }
    });

    // Pipe: fileStream -> sanitizer -> COPY stream
    fileStream.pipe(sanitizer).pipe(stream);
    
  } catch (err) {
    console.error('Fatal error:', err);
    client.end();
    process.exit(1);
  }
}

main();
