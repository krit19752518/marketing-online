import { Response } from 'express';
import { z } from 'zod';
import prisma from '../config/prisma.js';
import { AuthenticatedRequest } from '../middleware/auth.js';
import { OrderStatus, PaymentMethod } from '@prisma/client';

// Schemas
const orderItemInputSchema = z.object({
  productId: z.string().uuid(),
  quantity: z.number().int().positive(),
  notes: z.string().optional(),
  selectedOpts: z
    .array(
      z.object({
        name: z.string(),
        price: z.number().nonnegative(),
      })
    )
    .optional(),
});

const createOrderSchema = z.object({
  tableId: z.string().uuid().optional(),
  items: z.array(orderItemInputSchema).min(1),
});

const updateStatusSchema = z.object({
  status: z.nativeEnum(OrderStatus),
});

const checkoutSchema = z.object({
  paymentMethod: z.nativeEnum(PaymentMethod),
  amountPaid: z.number().nonnegative(),
  discount: z.number().nonnegative().default(0.0),
});

export const createOrder = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { tableId, items } = createOrderSchema.parse(req.body);

    // If tableId is provided, verify it exists and update its status
    if (tableId) {
      const table = await prisma.table.findUnique({ where: { id: tableId } });
      if (!table) {
        return res.status(404).json({ error: 'Table not found' });
      }
      await prisma.table.update({
        where: { id: tableId },
        data: { status: 'OCCUPIED' },
      });
    }

    // Process items and calculate total order price
    let totalAmount = 0;
    const orderItemsToCreate = [];

    for (const item of items) {
      const product = await prisma.product.findUnique({
        where: { id: item.productId },
      });

      if (!product) {
        return res.status(404).json({ error: `Product with ID ${item.productId} not found` });
      }

      // Calculate unit price including selected options
      const basePrice = product.price;
      const optionsPrice = item.selectedOpts?.reduce((acc, opt) => acc + opt.price, 0) || 0;
      const unitPrice = basePrice + optionsPrice;
      const subtotal = unitPrice * item.quantity;
      totalAmount += subtotal;

      orderItemsToCreate.push({
        productId: item.productId,
        quantity: item.quantity,
        notes: item.notes || null,
        selectedOpts: item.selectedOpts || [],
        subtotal,
      });
    }

    // Create the order inside a database transaction
    const order = await prisma.$transaction(async (tx) => {
      const createdOrder = await tx.order.create({
        data: {
          tableId: tableId || null,
          status: 'PENDING',
          totalAmount,
          items: {
            create: orderItemsToCreate,
          },
        },
        include: {
          items: {
            include: {
              product: {
                select: { name: true, price: true },
              },
            },
          },
        },
      });

      return createdOrder;
    });

    res.status(201).json(order);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to create order' });
  }
};

export const getOrders = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { status } = req.query;

    const orders = await prisma.order.findMany({
      where: status ? { status: status as OrderStatus } : {},
      include: {
        table: { select: { number: true } },
        items: {
          include: {
            product: { select: { name: true } },
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json(orders);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to retrieve orders' });
  }
};

export const getOrderById = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const order = await prisma.order.findUnique({
      where: { id },
      include: {
        table: { select: { number: true } },
        items: {
          include: {
            product: { select: { name: true, price: true } },
          },
        },
        transaction: true,
      },
    });

    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }

    res.json(order);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to retrieve order' });
  }
};

export const updateOrderStatus = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { status } = updateStatusSchema.parse(req.body);

    const order = await prisma.order.findUnique({ where: { id } });
    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }

    const updatedOrder = await prisma.$transaction(async (tx) => {
      const result = await tx.order.update({
        where: { id },
        data: { status },
      });

      // Synchronize table status if it's billing or cancelled
      if (order.tableId) {
        if (status === 'BILLING') {
          await tx.table.update({
            where: { id: order.tableId },
            data: { status: 'BILLING' },
          });
        } else if (status === 'CANCELLED') {
          await tx.table.update({
            where: { id: order.tableId },
            data: { status: 'VACANT' },
          });
        }
      }

      return result;
    });

    res.json(updatedOrder);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to update order status' });
  }
};

export const checkoutOrder = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { paymentMethod, amountPaid, discount } = checkoutSchema.parse(req.body);

    const order = await prisma.order.findUnique({
      where: { id },
      include: { items: true },
    });

    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }

    if (order.status === 'PAID') {
      return res.status(400).json({ error: 'Order has already been paid' });
    }

    const finalAmountDue = Math.max(0, order.totalAmount - discount);

    if (amountPaid < finalAmountDue) {
      return res.status(400).json({
        error: `Insufficient payment. Amount due: ${finalAmountDue}, Amount paid: ${amountPaid}`,
      });
    }

    const change = paymentMethod === 'CASH' ? amountPaid - finalAmountDue : 0.0;

    const result = await prisma.$transaction(async (tx) => {
      // 1. Create Transaction
      const transaction = await tx.transaction.create({
        data: {
          orderId: id,
          paymentMethod,
          amountPaid,
          discount,
          change,
        },
      });

      // 2. Deduct stock from inventory (matching by product name)
      for (const item of order.items) {
        const product = await tx.product.findUnique({
          where: { id: item.productId },
        });
        if (product) {
          const invItem = await tx.inventory.findUnique({
            where: { name: product.name },
          });
          if (invItem) {
            const newQty = invItem.quantity - item.quantity;
            if (newQty < 0) {
              throw new Error(`Insufficient stock for inventory item: ${invItem.name}`);
            }
            await tx.inventory.update({
              where: { id: invItem.id },
              data: { quantity: newQty },
            });
          }
        }
      }

      // 3. Set order status to PAID
      const updatedOrder = await tx.order.update({
        where: { id },
        data: { status: 'PAID' },
      });

      // 4. Set table status back to VACANT if applicable
      if (order.tableId) {
        await tx.table.update({
          where: { id: order.tableId },
          data: { status: 'VACANT' },
        });
      }

      return { updatedOrder, transaction };
    });

    res.json({
      message: 'Checkout completed successfully',
      order: result.updatedOrder,
      transaction: result.transaction,
    });
  } catch (error: any) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    if (error instanceof Error && error.message.startsWith('Insufficient stock')) {
      return res.status(400).json({ error: error.message });
    }
    console.error(error);
    res.status(500).json({ error: 'Failed to process checkout' });
  }
};
