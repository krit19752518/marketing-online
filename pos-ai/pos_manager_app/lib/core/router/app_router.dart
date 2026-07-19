import 'package:go_router/go_router.dart';
import '../../features/auth/login_screen.dart';
import '../../features/dashboard/dashboard_screen.dart';
import '../../features/menu/menu_management_screen.dart';
import '../../features/tables/tables_management_screen.dart';
import '../../features/inventory/inventory_screen.dart';
import '../../features/employees/employees_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/dashboard',
      builder: (context, state) => const DashboardScreen(),
    ),
    GoRoute(
      path: '/menu',
      builder: (context, state) => const MenuManagementScreen(),
    ),
    GoRoute(
      path: '/tables',
      builder: (context, state) => const TablesManagementScreen(),
    ),
    GoRoute(
      path: '/inventory',
      builder: (context, state) => const InventoryScreen(),
    ),
    GoRoute(
      path: '/employees',
      builder: (context, state) => const EmployeesScreen(),
    ),
  ],
);
