import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:pos_manager_app/providers/auth_provider.dart';
import 'package:pos_manager_app/features/dashboard/dashboard_screen.dart';

void main() {
  testWidgets('DashboardScreen renders loading state initially', (WidgetTester tester) async {
    // Set virtual screen size to avoid overflows in test run
    final dpi = tester.view.devicePixelRatio;
    tester.view.physicalSize = Size(1280 * dpi, 800 * dpi);

    addTearDown(() {
      tester.view.resetPhysicalSize();
    });

    final authProvider = AuthProvider();

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: authProvider,
        child: const MaterialApp(
          home: DashboardScreen(),
        ),
      ),
    );

    // Initial state before HTTP request returns should show loading indicator
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Verify Sidebar exists in layout
    expect(find.text('POS-AI Manager'), findsOneWidget);
  });
}
