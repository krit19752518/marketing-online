import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Table CRUD API Tests', () => {
  let ownerToken: string;
  let cashierToken: string;
  let tableId: string;

  const testOwner = {
    username: 'tableowner',
    password: 'password123',
    name: 'Table Owner',
    role: 'OWNER' as const,
  };

  const testCashier = {
    username: 'tablecashier',
    password: 'password123',
    name: 'Table Cashier',
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
    // Cleanup tables and users
    await prisma.table.deleteMany({});
    await prisma.user.deleteMany({
      where: {
        username: { in: [testOwner.username, testCashier.username] },
      },
    });
    await prisma.$disconnect();
  });

  it('should allow Owner to create table', async () => {
    const res = await request(app)
      .post('/api/tables')
      .set('Authorization', `Bearer ${ownerToken}`)
      .send({ number: 'A1' });

    expect(res.status).toBe(201);
    expect(res.body.number).toBe('A1');
    expect(res.body.status).toBe('VACANT');
    tableId = res.body.id;
  });

  it('should block Cashier from creating table', async () => {
    const res = await request(app)
      .post('/api/tables')
      .set('Authorization', `Bearer ${cashierToken}`)
      .send({ number: 'A2' });

    expect(res.status).toBe(403);
  });

  it('should allow anyone authenticated to view tables', async () => {
    const res = await request(app)
      .get('/api/tables')
      .set('Authorization', `Bearer ${cashierToken}`);

    expect(res.status).toBe(200);
    expect(res.body.length).toBeGreaterThanOrEqual(1);
    expect(res.body[0].number).toBe('A1');
  });

  it('should allow Cashier to update table status', async () => {
    const res = await request(app)
      .put(`/api/tables/${tableId}`)
      .set('Authorization', `Bearer ${cashierToken}`)
      .send({ number: 'A1', status: 'OCCUPIED' });

    expect(res.status).toBe(200);
    expect(res.body.status).toBe('OCCUPIED');
  });

  it('should block Cashier from deleting table', async () => {
    const res = await request(app)
      .delete(`/api/tables/${tableId}`)
      .set('Authorization', `Bearer ${cashierToken}`);

    expect(res.status).toBe(403);
  });

  it('should allow Owner to delete table', async () => {
    const res = await request(app)
      .delete(`/api/tables/${tableId}`)
      .set('Authorization', `Bearer ${ownerToken}`);

    expect(res.status).toBe(200);
    expect(res.body.message).toBe('Table deleted successfully');
  });
});
