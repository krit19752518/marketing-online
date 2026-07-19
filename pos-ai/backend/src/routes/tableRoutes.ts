import { Router } from 'express';
import {
  createTable,
  getTables,
  updateTable,
  deleteTable,
} from '../controllers/tableController.js';
import { authenticateJWT, authorizeRoles } from '../middleware/auth.js';

const router = Router();

router.post(
  '/tables',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  createTable
);
router.get('/tables', authenticateJWT, getTables);
router.put('/tables/:id', authenticateJWT, updateTable);
router.delete(
  '/tables/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  deleteTable
);

export default router;
