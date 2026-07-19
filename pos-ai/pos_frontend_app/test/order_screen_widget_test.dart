import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:pos_frontend_app/providers/catalog_provider.dart';
import 'package:pos_frontend_app/providers/cart_provider.dart';
import 'package:pos_frontend_app/features/orders/order_screen.dart';

void main() {
  testWidgets('OrderScreen renders empty cart initial state and controls', (WidgetTester tester) async {
    // Set a large screen size to prevent layout overflows in the test run
    final dpi = tester.view.devicePixelRatio;
    tester.view.physicalSize = Size(1280 * dpi, 800 * dpi);

    // Reset screen size after test
    addTearDown(() {
      tester.view.resetPhysicalSize();
    });

    final catalogProvider = CatalogProvider();
    final cartProvider = CartProvider();

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<CatalogProvider>.value(value: catalogProvider),
          ChangeNotifierProvider<CartProvider>.value(value: cartProvider),
        ],
        child: const MaterialApp(
          home: OrderScreen(tableNumber: '5'),
        ),
      ),
    );

    // Verify Title shows Table 5
    expect(find.text('Ordering: Table 5'), findsOneWidget);

    // Verify Empty state text is present in the cart sidebar
    expect(find.text('Cart is empty. Tap products to add.'), findsOneWidget);

    // Verify price calculations show 0.00 initially (Subtotal, VAT, and Total)
    expect(find.text('฿0.00'), findsNWidgets(3));

    // Verify checkout button is present and is disabled
    final checkoutButtonFinder = find.widgetWithText(ElevatedButton, 'Checkout (คิดเงิน)');
    expect(checkoutButtonFinder, findsOneWidget);
    
    final ElevatedButton checkoutButton = tester.widget(checkoutButtonFinder);
    expect(checkoutButton.enabled, false);
  });
}
