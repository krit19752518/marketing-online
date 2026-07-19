import { Response } from 'express';
import prisma from '../config/prisma.js';
import { AuthenticatedRequest } from '../middleware/auth.js';

export const getDashboardSummary = async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { startDate, endDate } = req.query;

    let dateFilter: any = {};
    if (startDate || endDate) {
      dateFilter.createdAt = {};
      if (startDate) {
        dateFilter.createdAt.gte = new Date(String(startDate));
      }
      if (endDate) {
        dateFilter.createdAt.lte = new Date(String(endDate));
      }
    }

    // 1. Total revenue and total orders
    const transactions = await prisma.transaction.findMany({
      where: startDate || endDate ? { createdAt: dateFilter.createdAt } : {},
      include: {
        order: true,
      },
    });

    const totalRevenue = transactions.reduce(
      (acc, t) => acc + (t.order.totalAmount - t.discount),
      0
    );
    const totalOrders = transactions.length;
    const averageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;

    // 2. Sales by Category
    const orderItems = await prisma.orderItem.findMany({
      where: {
        order: {
          status: 'PAID',
          ...(startDate || endDate ? { createdAt: dateFilter.createdAt } : {}),
        },
      },
      include: {
        product: {
          include: {
            category: true,
          },
        },
      },
    });

    const categorySalesMap: Record<string, number> = {};
    const productSalesMap: Record<
      string,
      { name: string; quantity: number; revenue: number }
    > = {};

    for (const item of orderItems) {
      const catName = item.product.category.name;
      categorySalesMap[catName] = (categorySalesMap[catName] || 0) + item.subtotal;

      const prodId = item.productId;
      if (!productSalesMap[prodId]) {
        productSalesMap[prodId] = {
          name: item.product.name,
          quantity: 0,
          revenue: 0,
        };
      }
      productSalesMap[prodId].quantity += item.quantity;
      productSalesMap[prodId].revenue += item.subtotal;
    }

    const salesByCategory = Object.entries(categorySalesMap).map(([name, revenue]) => ({
      name,
      revenue,
    }));

    // 3. Top Selling Products
    const topProducts = Object.values(productSalesMap)
      .sort((a, b) => b.quantity - a.quantity)
      .slice(0, 5);

    // 4. Daily Sales Chart Data (Group by date for the last 7 days or matching range)
    const dailySalesMap: Record<string, { revenue: number; orders: number }> = {};

    for (const t of transactions) {
      const dateStr = t.createdAt.toISOString().split('T')[0];
      if (!dailySalesMap[dateStr]) {
        dailySalesMap[dateStr] = { revenue: 0, orders: 0 };
      }
      dailySalesMap[dateStr].revenue += t.amountPaid - t.discount;
      dailySalesMap[dateStr].orders += 1;
    }

    const dailySales = Object.entries(dailySalesMap)
      .map(([date, data]) => ({
        date,
        revenue: data.revenue,
        orders: data.orders,
      }))
      .sort((a, b) => a.date.localeCompare(b.date));

    res.json({
      totalRevenue,
      totalOrders,
      averageOrderValue,
      salesByCategory,
      topProducts,
      dailySales,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to retrieve analytics dashboard summary' });
  }
};
