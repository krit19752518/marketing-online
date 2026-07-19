import { Router } from 'express';
import { register, login, getMe, getUsers, updateUser, deleteUser } from '../controllers/authController.js';
import { authenticateJWT } from '../middleware/auth.js';

const router = Router();

router.post('/register', register);
router.post('/login', login);
router.get('/me', authenticateJWT, getMe);

router.get('/users', authenticateJWT, getUsers);
router.put('/users/:id', authenticateJWT, updateUser);
router.delete('/users/:id', authenticateJWT, deleteUser);

export default router;
