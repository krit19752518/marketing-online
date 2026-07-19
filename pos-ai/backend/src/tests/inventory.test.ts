import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Inventory & Stock Management Tests', () => {
  let ownerToken: string;
  let cashierToken: string;
  let categoryId: string;
  let productId: string;
  let inventoryItemId: string;

  const testOwner = {
    username: 'invowner',
    password: 'password123',
    name: 'Inventory Owner',
    role: 'OWNER' as const,
  };

  const testCashier = {
    username: 'invcashier',
    password: 'password123',
    name: 'Inventory Cashier',
    role: 'CASHIER' as const,
  };

  beforeAll(async () => {
    // Cleanup existing users
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

    // Create Category and Product
    const cat = await prisma.category.create({ data: { name: 'Pastries' } });
    categoryId = cat.id;

    const prod = await prisma.product.create({
      data: {
        name: 'Croissant',
        price: 45.0,
        categoryId: categoryId,
      },
    });
    productId = prod.id;
  });

  afterAll(async () => {
    // Cleanup databases
    await prisma.transaction.deleteMany({});
    await prisma.orderItem.deleteMany({});
    await prisma.order.deleteMany({});
    await prisma.inventory.deleteMany({});
    await prisma.product.deleteMany({});
    await prisma.category.deleteMany({});
    await prisma.user.deleteMany({
      where: {
        username: { in: [testOwner.username, testCashier.username] },
      },
    });
    await prisma.$disconnect();
  });

  describe('Inventory CRUD & Adjustments', () => {
    it('should allow Owner to create inventory item', async () => {
      const res = await request(app)
        .post('/api/inventory')
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({
          name: 'Croissant',
          quantity: 10,
          unit: 'pcs',
          minQuantity: 3,
        });

      expect(res.status).toBe(201);
      expect(res.body.name).toBe('Croissant');
      expect(res.body.quantity).toBe(10);
      inventoryItemId = res.body.id;
    });

    it('should block Cashier from creating inventory item', async () => {
      const res = await request(app)
        .post('/api/inventory')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          name: 'Butter',
          quantity: 5,
          unit: 'kg',
        });

      expect(res.status).toBe(403);
    });

    it('should allow Owner to adjust stock manually', async () => {
      const res = await request(app)
        .post(`/api/inventory/${inventoryItemId}/adjust`)
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({ quantity: 5 }); // add 5

      expect(res.status).toBe(200);
      expect(res.body.quantity).toBe(15);
    });

    it('should fail adjustment if it results in negative stock', async () => {
      const res = await request(app)
        .post(`/api/inventory/${inventoryItemId}/adjust`)
        .set('Authorization', `Bearer ${ownerToken}`)
        .send({ quantity: -20 }); // subtract 20 (current is 15)

      expect(res.status).toBe(400);
      expect(res.body.error).toContain('Adjustment would result in negative stock');
    });
  });

  describe('Stock Deduction on Checkout', () => {
    it('should deduct stock on successful checkout', async () => {
      // 1. Create order for 3 Croissants
      const orderRes = await request(app)
        .post('/api/orders')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          items: [{ productId, quantity: 3 }],
        });
      const orderId = orderRes.body.id;

      // 2. Checkout
      const checkoutRes = await request(app)
        .post(`/api/orders/${orderId}/checkout`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          paymentMethod: 'CASH',
          amountPaid: 200.0,
        });

      expect(checkoutRes.status).toBe(200);

      // 3. Verify stock is reduced from 15 to 12
      const invItem = await prisma.inventory.findUnique({
        where: { id: inventoryItemId },
      });
      expect(invItem?.quantity).toBe(12);
    });

    it('should fail checkout if order quantity exceeds available stock', async () => {
      // Current stock is 12. Create order for 15 Croissants
      const orderRes = await request(app)
        .post('/api/orders')
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          items: [{ productId, quantity: 15 }],
        });
      const orderId = orderRes.body.id;

      // Checkout should fail due to stock limit
      const checkoutRes = await request(app)
        .post(`/api/orders/${orderId}/checkout`)
        .set('Authorization', `Bearer ${cashierToken}`)
        .send({
          paymentMethod: 'CASH',
          amountPaid: 1000.0,
        });

      expect(checkoutRes.status).toBe(400);
      expect(checkoutRes.body.error).toContain('Insufficient stock for inventory item: Croissant');
    });
  });
});
