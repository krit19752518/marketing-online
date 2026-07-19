import { Router } from 'express';
import {
  createInventoryItem,
  getInventoryItems,
  updateInventoryItem,
  adjustStock,
  deleteInventoryItem,
} from '../controllers/inventoryController.js';
import { authenticateJWT, authorizeRoles } from '../middleware/auth.js';

const router = Router();

router.post(
  '/inventory',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  createInventoryItem
);
router.get('/inventory', authenticateJWT, getInventoryItems);
router.put(
  '/inventory/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  updateInventoryItem
);
router.post(
  '/inventory/:id/adjust',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  adjustStock
);
router.delete(
  '/inventory/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  deleteInventoryItem
);

export default router;
