import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Product & Category CRUD API Tests', () => {
  let ownerToken: string;
  let cashierToken: string;
  let categoryId: string;
  let productId: string;

  const testOwner = {
    username: 'prodowner',
    password: 'password123',
    name: 'Prod Owner',
    role: 'OWNER' as const,
  };

  const testCashier = {
    username: 'prodcashier',
    password: 'password123',
    name: 'Prod Cashier',
    role: 'CASHIER' as const,
  };

  beforeAll(async () => {
    // Cleanup any existing test users
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
  });

  afterAll(async () => {
    // Cleanup products, categories, users
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

  describe('Category Endpoints', () => {
    it('should allow Owner to create category', async () => {
      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({ name: 'Drinks' });

      expect(res.status).toBe(201);
      expect(res.body.name).toBe('Drinks');
      categoryId = res.body.id;
    });

    it('should block Cashier from creating category', async () => {
      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({ name: 'Food' });

      expect(res.status).toBe(403);
    });

    it('should allow anyone authenticated to view categories', async () => {
      const res = await request(app)
        .get('/api/categories')
        .set('Authorization', `Bearer ${cashierToken}`);

      expect(res.status).toBe(200);
      expect(res.body.length).toBeGreaterThanOrEqual(1);
      expect(res.body[0].name).toBe('Drinks');
    });
  });

  describe('Product Endpoints', () => {
    it('should allow Owner to create product with options', async () => {
      const res = await request(app)
        .post('/api/products')
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({
          name: 'Iced Latte',
          price: 65.0,
          categoryId: categoryId,
          imageUrl: 'http://example.com/latte.jpg',
          options: [
            { name: 'Sweetness 50%', price: 0.0 },
            { name: 'Extra Shot', price: 15.0 },
          ],
        });

      expect(res.status).toBe(201);
      expect(res.body.name).toBe('Iced Latte');
      expect(res.body.options.length).toBe(2);
      productId = res.body.id;
    });

    it('should block Cashier from creating product', async () => {
      const res = await request(app)
        .post('/api/products')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          name: 'Mock Espresso',
          price: 50.0,
          categoryId: categoryId,
        });

      expect(res.status).toBe(403);
    });

    it('should get all products', async () => {
      const res = await request(app)
        .get('/api/products')
        .set('Authorization', `Bearer ${cashierToken}`);

      expect(res.status).toBe(200);
      expect(res.body.length).toBeGreaterThanOrEqual(1);
      expect(res.body[0].name).toBe('Iced Latte');
      expect(res.body[0].options.length).toBe(2);
    });

    it('should allow Owner to update product details and options', async () => {
      const res = await request(app)
        .put(`/api/products/${productId}`)
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({
          name: 'Iced Latte Special',
          price: 70.0,
          categoryId: categoryId,
          options: [
            { name: 'Sweetness 0%', price: 0.0 },
          ],
        });

      expect(res.status).toBe(200);
      expect(res.body.name).toBe('Iced Latte Special');
      expect(res.body.price).toBe(70.0);
      expect(res.body.options.length).toBe(1);
      expect(res.body.options[0].name).toBe('Sweetness 0%');
    });

    it('should allow Owner to delete product', async () => {
      const res = await request(app)
        .delete(`/api/products/${productId}`)
        .set('Authorization', `Bearer ${ownerToken}`);

      expect(res.status).toBe(200);
      expect(res.body.message).toBe('Product deleted successfully');
    });
  });
});
