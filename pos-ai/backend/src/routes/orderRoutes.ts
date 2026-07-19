import { Router } from 'express';
import {
  createOrder,
  getOrders,
  getOrderById,
  updateOrderStatus,
  checkoutOrder,
} from '../controllers/orderController.js';
import { authenticateJWT, authorizeRoles } from '../middleware/auth.js';

const router = Router();

router.post('/orders', authenticateJWT, createOrder);
router.get('/orders', authenticateJWT, getOrders);
router.get('/orders/:id', authenticateJWT, getOrderById);
router.put('/orders/:id/status', authenticateJWT, updateOrderStatus);
router.post(
  '/orders/:id/checkout',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER', 'CASHIER'),
  checkoutOrder
);

export default router;
