import { Response } from 'express';
import { z } from 'zod';
import prisma from '../config/prisma.js';
import { AuthenticatedRequest } from '../middleware/auth.js';

// Schemas
const tableSchema = z.object({
  number: z.string().min(1),
  status: z.enum(['VACANT', 'OCCUPIED', 'BILLING']).optional(),
});

export const createTable = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { number, status } = tableSchema.parse(req.body);

    const existing = await prisma.table.findUnique({ where: { number } });
    if (existing) {
      return res.status(400).json({ error: 'Table number already exists' });
    }

    const table = await prisma.table.create({
      data: {
        number,
        status: status || 'VACANT',
      },
    });

    res.status(201).json(table);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getTables = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const tables = await prisma.table.findMany({
      orderBy: { number: 'asc' },
    });
    res.json(tables);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateTable = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { number, status } = tableSchema.parse(req.body);

    // If updating number, ensure uniqueness
    if (number) {
      const existing = await prisma.table.findFirst({
        where: {
          number,
          NOT: { id },
        },
      });
      if (existing) {
        return res.status(400).json({ error: 'Table number already exists' });
      }
    }

    const table = await prisma.table.update({
      where: { id },
      data: {
        number,
        status,
      },
    });

    res.json(table);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to update table' });
  }
};

export const deleteTable = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    await prisma.table.delete({ where: { id } });
    res.json({ message: 'Table deleted successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to delete table' });
  }
};
