import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import app from '../app.js';
import prisma from '../config/prisma.js';

describe('Auth & Role Authorization API Tests', () => {
  const testUser = {
    username: 'testcashier',
    password: 'password123',
    name: 'Test Cashier',
    role: 'CASHIER' as const,
  };

  const testOwner = {
    username: 'testowner',
    password: 'password123',
    name: 'Test Owner',
    role: 'OWNER' as const,
  };

  beforeAll(async () => {
    // Clean up test users if they exist
    await prisma.user.deleteMany({
      where: {
        username: {
          in: [testUser.username, testOwner.username],
        },
      },
    });
  });

  afterAll(async () => {
    // Clean up databases
    await prisma.user.deleteMany({
      where: {
        username: {
          in: [testUser.username, testOwner.username],
        },
      },
    });
    await prisma.$disconnect();
  });

  describe('POST /api/auth/register', () => {
    it('should register a new user successfully', async () => {
      const res = await request(app)
        .post('/api/auth/register')
        .send(testUser);

      expect(res.status).toBe(201);
      expect(res.body.user).toBeDefined();
      expect(res.body.user.username).toBe(testUser.username);
      expect(res.body.user.role).toBe(testUser.role);
      expect(res.body.user.password).toBeUndefined(); // Password shouldn't be returned
    });

    it('should fail registration with duplicate username', async () => {
      const res = await request(app)
        .post('/api/auth/register')
        .send(testUser);

      expect(res.status).toBe(400);
      expect(res.body.error).toContain('Username is already taken');
    });

    it('should fail registration with invalid input', async () => {
      const res = await request(app)
        .post('/api/auth/register')
        .send({
          username: 'a', // Too short
          password: '12', // Too short
          name: '', // Empty
        });

      expect(res.status).toBe(400);
      expect(res.body.error).toBe('Validation failed');
    });
  });

  describe('POST /api/auth/login', () => {
    beforeAll(async () => {
      // Register test owner
      await request(app)
        .post('/api/auth/register')
        .send(testOwner);
    });

    it('should login successfully with correct credentials', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send({
          username: testUser.username,
          password: testUser.password,
        });

      expect(res.status).toBe(200);
      expect(res.body.token).toBeDefined();
      expect(res.body.user.username).toBe(testUser.username);
    });

    it('should fail login with incorrect password', async () => {
      const res = await request(app)
        .post('/api/auth/login')
        .send({
          username: testUser.username,
          password: 'wrongpassword',
        });

      expect(res.status).toBe(401);
      expect(res.body.error).toContain('Invalid username or password');
    });
  });

  describe('GET /api/auth/me (Protected)', () => {
    let cashierToken: string;
    let ownerToken: string;

    beforeAll(async () => {
      const cashierRes = await request(app)
        .post('/api/auth/login')
        .send({
          username: testUser.username,
          password: testUser.password,
        });
      cashierToken = cashierRes.body.token;

      const ownerRes = await request(app)
        .post('/api/auth/login')
        .send({
          username: testOwner.username,
          password: testOwner.password,
        });
      ownerToken = ownerRes.body.token;
    });

    it('should return user info when correct token is supplied', async () => {
      const res = await request(app)
        .get('/api/auth/me')
        .set('Authorization', `Bearer ${cashierToken}`);

      expect(res.status).toBe(200);
      expect(res.body.username).toBe(testUser.username);
      expect(res.body.role).toBe(testUser.role);
    });

    it('should block access if authorization header is missing', async () => {
      const res = await request(app).get('/api/auth/me');

      expect(res.status).toBe(401);
      expect(res.body.error).toContain('Authorization header with Bearer token is required');
    });

    it('should block access if token is invalid', async () => {
      const res = await request(app)
        .get('/api/auth/me')
        .set('Authorization', 'Bearer invalidtoken123');

      expect(res.status).toBe(403);
      expect(res.body.error).toContain('Invalid or expired token');
    });
  });
});
