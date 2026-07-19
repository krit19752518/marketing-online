import { Router } from 'express';
import {
  createCategory,
  getCategories,
  updateCategory,
  deleteCategory,
  createProduct,
  getProducts,
  updateProduct,
  deleteProduct,
} from '../controllers/productController.js';
import { authenticateJWT, authorizeRoles } from '../middleware/auth.js';

const router = Router();

// Category Routes
router.post(
  '/categories',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  createCategory
);
router.get('/categories', authenticateJWT, getCategories);
router.put(
  '/categories/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  updateCategory
);
router.delete(
  '/categories/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  deleteCategory
);

// Product Routes
router.post(
  '/products',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  createProduct
);
router.get('/products', authenticateJWT, getProducts);
router.put(
  '/products/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  updateProduct
);
router.delete(
  '/products/:id',
  authenticateJWT,
  authorizeRoles('OWNER', 'MANAGER'),
  deleteProduct
);

export default router;
