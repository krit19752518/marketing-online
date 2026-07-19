import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Analytics & Report API Tests', () => {
  let ownerToken: string;
  let cashierToken: string;
  let categoryId: string;
  let productId: string;
  let orderId: string;

  const testOwner = {
    username: 'analowner',
    password: 'password123',
    name: 'Analytics Owner',
    role: 'OWNER' as const,
  };

  const testCashier = {
    username: 'analcashier',
    password: 'password123',
    name: 'Analytics Cashier',
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

    // Seed mock category and product
    const cat = await prisma.category.create({ data: { name: 'Bakery' } });
    categoryId = cat.id;

    const prod = await prisma.product.create({
      data: {
        name: 'Muffin',
        price: 50.0,
        categoryId: categoryId,
      },
    });
    productId = prod.id;

    // Create a paid transaction to populate analytics
    const order = await prisma.order.create({
      data: {
        status: 'PAID',
        totalAmount: 100.0,
        items: {
          create: [
            {
              productId: productId,
              quantity: 2,
              subtotal: 100.0,
            },
          ],
        },
      },
    });
    orderId = order.id;

    await prisma.transaction.create({
      data: {
        orderId: orderId,
        paymentMethod: 'CASH',
        amountPaid: 100.0,
        discount: 0.0,
        change: 0.0,
      },
    });
  });

  afterAll(async () => {
    // Cleanup database
    await prisma.transaction.deleteMany({});
    await prisma.orderItem.deleteMany({});
    await prisma.order.deleteMany({});
    await prisma.product.deleteMany({});
    await prisma.category.deleteMany({});
    await prisma.user.deleteMany({
      where: {
        username: { in: [testOwner.username, testCashier.username] },
      },
    });
    await prisma.$disconnect();
  });

  it('should block Cashier from accessing analytics summary', async () => {
    const res = await request(app)
      .get('/api/analytics/dashboard')
      .set('Authorization', `Bearer ${cashierToken}`);

    expect(res.status).toBe(403);
  });

  it('should allow Owner to view analytics summary and return correct sales totals', async () => {
    const res = await request(app)
      .get('/api/analytics/dashboard')
      .set('Authorization', `Bearer ${ownerToken}`);

    expect(res.status).toBe(200);
    expect(res.body.totalRevenue).toBe(100.0);
    expect(res.body.totalOrders).toBe(1);
    expect(res.body.averageOrderValue).toBe(100.0);
    expect(res.body.salesByCategory.length).toBeGreaterThanOrEqual(1);
    expect(res.body.salesByCategory[0].name).toBe('Bakery');
    expect(res.body.salesByCategory[0].revenue).toBe(100.0);
    expect(res.body.topProducts[0].name).toBe('Muffin');
    expect(res.body.topProducts[0].quantity).toBe(2);
  });
});
