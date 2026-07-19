import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:pos_frontend_app/providers/auth_provider.dart';
import 'package:pos_frontend_app/features/auth/login_screen.dart';

void main() {
  testWidgets('LoginScreen renders fields and login button', (WidgetTester tester) async {
    final authProvider = AuthProvider();

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: authProvider,
        child: const MaterialApp(
          home: LoginScreen(),
        ),
      ),
    );

    // Verify Title and Subtitle are present
    expect(find.text('POS-AI Terminal'), findsOneWidget);
    expect(find.text('Sign in to access your cashier terminal'), findsOneWidget);

    // Verify TextFields are present
    expect(find.widgetWithText(TextFormField, 'Username'), findsOneWidget);
    expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);

    // Verify Sign In Button is present
    expect(find.widgetWithText(ElevatedButton, 'Sign In'), findsOneWidget);
  });
}
