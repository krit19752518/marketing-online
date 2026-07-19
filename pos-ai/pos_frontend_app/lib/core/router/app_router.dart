import 'package:go_router/go_router.dart';
import '../../features/auth/login_screen.dart';
import '../../features/tables/tables_screen.dart';
import '../../features/orders/order_screen.dart';
import '../../features/billing/checkout_screen.dart';
import '../../features/kitchen/kitchen_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/tables',
      builder: (context, state) => const TablesScreen(),
    ),
    GoRoute(
      path: '/order',
      builder: (context, state) {
        final tableId = state.uri.queryParameters['tableId'];
        final tableNumber = state.uri.queryParameters['tableNumber'];
        final tableStatus = state.uri.queryParameters['tableStatus'];
        return OrderScreen(
          tableId: tableId,
          tableNumber: tableNumber,
          tableStatus: tableStatus,
        );
      },
    ),
    GoRoute(
      path: '/checkout',
      builder: (context, state) {
        final orderId = state.uri.queryParameters['orderId'] ?? '';
        return CheckoutScreen(orderId: orderId);
      },
    ),
    GoRoute(
      path: '/kitchen',
      builder: (context, state) => const KitchenScreen(),
    ),
  ],
);
