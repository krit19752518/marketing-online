import { Router } from 'express';
import { getDashboardSummary } from '../controllers/analyticsController.js';
import { authenticateJWT, authorizeRoles } from '../middleware/auth.js';

const router = Router();

router.get(
  '/analytics/dashboard',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  getDashboardSummary
);

export default router;
