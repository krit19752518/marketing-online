import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Order & Billing API Tests', () => {
  let ownerToken: string;
  let cashierToken: string;
  let categoryId: string;
  let productId: string;
  let tableId: string;
  let orderId: string;

  const testOwner = {
    username: 'orderowner',
    password: 'password123',
    name: 'Order Owner',
    role: 'OWNER' as const,
  };

  const testCashier = {
    username: 'ordercashier',
    password: 'password123',
    name: 'Order Cashier',
    role: 'CASHIER' as const,
  };

  beforeAll(async () => {
    // Cleanup existing data
    await prisma.user.deleteMany({
      where: {
        username: { in: [testOwner.username, testCashier.username] },
      },
    });

    // Register & Login Owner
    await request(app).post('/api/auth/register').send(testOwner);
    const ownerLogin = await request(app).post('/api/auth/login').send({
      username: testOwner.username,
      password: testOwner.password,
    });
    ownerToken = ownerLogin.body.token;

    // Register & Login Cashier
    await request(app).post('/api/auth/register').send(testCashier);
    const cashierLogin = await request(app).post('/api/auth/login').send({
      username: testCashier.username,
      password: testCashier.password,
    });
    cashierToken = cashierLogin.body.token;

    // Create Category, Product, Table
    const cat = await prisma.category.create({ data: { name: 'Desserts' } });
    categoryId = cat.id;

    const prod = await prisma.product.create({
      data: {
        name: 'Chocolate Cake',
        price: 90.0,
        categoryId: categoryId,
        options: {
          create: [
            { name: 'Extra Ice Cream', price: 20.0 },
            { name: 'Less Sweet', price: 0.0 },
          ],
        },
      },
      include: { options: true },
    });
    productId = prod.id;

    const tbl = await prisma.table.create({ data: { number: 'B1' } });
    tableId = tbl.id;
  });

  afterAll(async () => {
    // Cleanup everything
    await prisma.transaction.deleteMany({});
    await prisma.orderItem.deleteMany({});
    await prisma.order.deleteMany({});
    await prisma.table.deleteMany({});
    await prisma.productOption.deleteMany({});
    await prisma.product.deleteMany({});
    await prisma.category.deleteMany({});
    await prisma.user.deleteMany({
      where: {
        username: { in: [testOwner.username, testCashier.username] },
      },
    });
    await prisma.$disconnect();
  });

  describe('POST /api/orders', () => {
    it('should create a dine-in order and mark table as OCCUPIED', async () => {
      const res = await request(app)
        .post('/api/orders')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          tableId,
          items: [
            {
              productId,
              quantity: 2,
              notes: 'Serve with warm water',
              selectedOpts: [
                { name: 'Extra Ice Cream', price: 20.0 },
                { name: 'Less Sweet', price: 0.0 },
              ],
            },
          ],
        });

      expect(res.status).toBe(201);
      expect(res.body.status).toBe('PENDING');
      // Price calculation: (90.0 base + 20.0 option + 0.0 option) * 2 quantity = 220.0 total
      expect(res.body.totalAmount).toBe(220.0);
      expect(res.body.items.length).toBe(1);
      expect(res.body.items[0].subtotal).toBe(220.0);
      orderId = res.body.id;

      // Verify table status is updated to OCCUPIED
      const table = await prisma.table.findUnique({ where: { id: tableId } });
      expect(table?.status).toBe('OCCUPIED');
    });
  });

  describe('PUT /api/orders/:id/status', () => {
    it('should allow updating order status to BILLING and update table status', async () => {
      const res = await request(app)
        .put(`/api/orders/${orderId}/status`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({ status: 'BILLING' });

      expect(res.status).toBe(200);
      expect(res.body.status).toBe('BILLING');

      // Verify table status is updated to BILLING
      const table = await prisma.table.findUnique({ where: { id: tableId } });
      expect(table?.status).toBe('BILLING');
    });
  });

  describe('POST /api/orders/:id/checkout', () => {
    it('should fail checkout if amount paid is insufficient', async () => {
      const res = await request(app)
        .post(`/api/orders/${orderId}/checkout`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          paymentMethod: 'CASH',
          amountPaid: 150.0, // Order total is 220.0
          discount: 10.0, // Remaining due is 210.0
        });

      expect(res.status).toBe(400);
      expect(res.body.error).toContain('Insufficient payment');
    });

    it('should succeed checkout with correct details, generate transaction, and vacate table', async () => {
      const res = await request(app)
        .post(`/api/orders/${orderId}/checkout`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          paymentMethod: 'CASH',
          amountPaid: 250.0,
          discount: 20.0, // Remaining due is 200.0
        });

      expect(res.status).toBe(200);
      expect(res.body.message).toBe('Checkout completed successfully');
      expect(res.body.order.status).toBe('PAID');
      expect(res.body.transaction.amountPaid).toBe(250.0);
      expect(res.body.transaction.discount).toBe(20.0);
      expect(res.body.transaction.change).toBe(50.0); // 250 - 200 = 50 change

      // Verify table status is updated back to VACANT
      const table = await prisma.table.findUnique({ where: { id: tableId } });
      expect(table?.status).toBe('VACANT');
    });

    it('should block duplicate checkout', async () => {
      const res = await request(app)
        .post(`/api/orders/${orderId}/checkout`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          paymentMethod: 'CASH',
          amountPaid: 220.0,
        });

      expect(res.status).toBe(400);
      expect(res.body.error).toContain('Order has already been paid');
    });
  });
});
