import { Response } from 'express';
import { z } from 'zod';
import prisma from '../config/prisma.js';
import { AuthenticatedRequest } from '../middleware/auth.js';

// Schemas
const inventorySchema = z.object({
  name: z.string().min(1),
  quantity: z.number().nonnegative().default(0.0),
  unit: z.string().min(1),
  minQuantity: z.number().nonnegative().default(0.0),
});

const adjustStockSchema = z.object({
  quantity: z.number(), // positive to add, negative to subtract
});

export const createInventoryItem = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const body = inventorySchema.parse(req.body);

    const existing = await prisma.inventory.findUnique({
      where: { name: body.name },
    });

    if (existing) {
      return res.status(400).json({ error: 'Inventory item name already exists' });
    }

    const item = await prisma.inventory.create({
      data: body,
    });

    res.status(201).json(item);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getInventoryItems = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const items = await prisma.inventory.findMany({
      orderBy: { name: 'asc' },
    });
    res.json(items);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateInventoryItem = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const body = inventorySchema.parse(req.body);

    const existing = await prisma.inventory.findFirst({
      where: {
        name: body.name,
        NOT: { id },
      },
    });

    if (existing) {
      return res.status(400).json({ error: 'Inventory item name already exists' });
    }

    const item = await prisma.inventory.update({
      where: { id },
      data: body,
    });

    res.json(item);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to update inventory item' });
  }
};

export const adjustStock = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { quantity } = adjustStockSchema.parse(req.body);

    const item = await prisma.inventory.findUnique({ where: { id } });
    if (!item) {
      return res.status(404).json({ error: 'Inventory item not found' });
    }

    const newQuantity = item.quantity + quantity;
    if (newQuantity < 0) {
      return res.status(400).json({ error: 'Adjustment would result in negative stock' });
    }

    const updatedItem = await prisma.inventory.update({
      where: { id },
      data: { quantity: newQuantity },
    });

    res.json(updatedItem);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to adjust stock' });
  }
};

export const deleteInventoryItem = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    await prisma.inventory.delete({ where: { id } });
    res.json({ message: 'Inventory item deleted successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to delete inventory item' });
  }
};
