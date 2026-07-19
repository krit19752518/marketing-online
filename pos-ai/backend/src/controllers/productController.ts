import { Response } from 'express';
import { z } from 'zod';
import prisma from '../config/prisma.js';
import { AuthenticatedRequest } from '../middleware/auth.js';

// Schemas
const categorySchema = z.object({
  name: z.string().min(1),
});

const productOptionSchema = z.object({
  name: z.string().min(1),
  price: z.number().nonnegative().default(0.0),
});

const productSchema = z.object({
  name: z.string().min(1),
  price: z.number().positive(),
  imageUrl: z.string().url().optional().nullable(),
  categoryId: z.string().uuid(),
  options: z.array(productOptionSchema).optional(),
});

// CATEGORY CONTROLLERS
export const createCategory = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { name } = categorySchema.parse(req.body);

    const existing = await prisma.category.findUnique({ where: { name } });
    if (existing) {
      return res.status(400).json({ error: 'Category name already exists' });
    }

    const category = await prisma.category.create({
      data: { name },
    });

    res.status(201).json(category);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getCategories = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const categories = await prisma.category.findMany({
      include: {
        _count: {
          select: { products: true },
        },
      },
      orderBy: { name: 'asc' },
    });
    res.json(categories);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateCategory = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { name } = categorySchema.parse(req.body);

    const category = await prisma.category.update({
      where: { id },
      data: { name },
    });

    res.json(category);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    // Handle prisma error (not found)
    console.error(error);
    res.status(500).json({ error: 'Failed to update category' });
  }
};

export const deleteCategory = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    await prisma.category.delete({ where: { id } });
    res.json({ message: 'Category deleted successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to delete category' });
  }
};

// PRODUCT CONTROLLERS
export const createProduct = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const body = productSchema.parse(req.body);

    const categoryExists = await prisma.category.findUnique({
      where: { id: body.categoryId },
    });

    if (!categoryExists) {
      return res.status(400).json({ error: 'Category not found' });
    }

    const product = await prisma.product.create({
      data: {
        name: body.name,
        price: body.price,
        imageUrl: body.imageUrl,
        categoryId: body.categoryId,
        options: {
          create: body.options || [],
        },
      },
      include: {
        options: true,
      },
    });

    res.status(201).json(product);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getProducts = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { categoryId } = req.query;

    const products = await prisma.product.findMany({
      where: categoryId ? { categoryId: String(categoryId) } : {},
      include: {
        options: true,
        category: {
          select: { name: true },
        },
      },
      orderBy: { name: 'asc' },
    });

    res.json(products);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const updateProduct = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const body = productSchema.parse(req.body);

    // Delete existing options first and recreate them
    await prisma.productOption.deleteMany({
      where: { productId: id },
    });

    const product = await prisma.product.update({
      where: { id },
      data: {
        name: body.name,
        price: body.price,
        imageUrl: body.imageUrl,
        categoryId: body.categoryId,
        options: {
          create: body.options || [],
        },
      },
      include: {
        options: true,
      },
    });

    res.json(product);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to update product' });
  }
};

export const deleteProduct = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    await prisma.product.delete({ where: { id } });
    res.json({ message: 'Product deleted successfully' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to delete product' });
  }
};
