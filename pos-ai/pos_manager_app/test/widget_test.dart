import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:pos_manager_app/providers/auth_provider.dart';
import 'package:pos_manager_app/features/auth/login_screen.dart';

void main() {
  testWidgets('Manager LoginScreen renders branding and input elements', (WidgetTester tester) async {
    // Set a large screen size to prevent layout overflows in the test run
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
          home: LoginScreen(),
        ),
      ),
    );

    // Verify Manager Branding text is present
    expect(find.text('POS-AI Manager Panel'), findsOneWidget);
    expect(find.text('Real-time retail analytics, staff scheduling, inventory adjustments, and menu catalogs management.'), findsOneWidget);

    // Verify Manager Login fields are present
    expect(find.widgetWithText(TextFormField, 'Username'), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);

    // Verify Sign In Button is present
    expect(find.widgetWithText(ElevatedButton, 'Sign In'), findsOneWidget);
  });
}
