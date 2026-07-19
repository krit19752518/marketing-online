import 'package:flutter_test/flutter_test.dart';
import 'package:pos_frontend_app/models/product_model.dart';
import 'package:pos_frontend_app/providers/cart_provider.dart';

void main() {
  group('CartProvider Unit Tests', () {
    late CartProvider cartProvider;
    late ProductModel testProduct1;
    late ProductModel testProduct2;
    late ProductOptionModel testOption1;
    late ProductOptionModel testOption2;

    setUp(() {
      cartProvider = CartProvider();

      testOption1 = ProductOptionModel(
        id: 'opt1',
        name: 'Extra Whipped Cream',
        price: 15.0,
      );
      testOption2 = ProductOptionModel(
        id: 'opt2',
        name: 'Less Sweet',
        price: 0.0,
      );

      testProduct1 = ProductModel(
        id: 'p1',
        name: 'Iced Cappuccino',
        price: 60.0,
        categoryId: 'cat1',
        options: [testOption1, testOption2],
      );

      testProduct2 = ProductModel(
        id: 'p2',
        name: 'Brownie',
        price: 40.0,
        categoryId: 'cat2',
        options: [],
      );
    });

    test('Initial cart should be empty', () {
      expect(cartProvider.items.isEmpty, true);
      expect(cartProvider.subtotalAmount, 0.0);
      expect(cartProvider.vatAmount, 0.0);
      expect(cartProvider.totalAmount, 0.0);
    });

    test('Adding product without options to cart should add new item', () {
      cartProvider.addToCart(testProduct2, 2, [], null);

      expect(cartProvider.items.length, 1);
      expect(cartProvider.items[0].product.id, 'p2');
      expect(cartProvider.items[0].quantity, 2);
      expect(cartProvider.items[0].selectedOptions.isEmpty, true);
      expect(cartProvider.items[0].notes, null);

      // Calculations: 40 * 2 = 80 subtotal. VAT = 80 * 0.07 = 5.6. Total = 85.6
      expect(cartProvider.subtotalAmount, 80.0);
      expect(cartProvider.vatAmount, closeTo(5.6, 0.0001));
      expect(cartProvider.totalAmount, closeTo(85.6, 0.0001));
    });

    test('Adding product with options and notes should calculate correctly', () {
      cartProvider.addToCart(
        testProduct1,
        1,
        [testOption1],
        'Extra hot',
      );

      expect(cartProvider.items.length, 1);
      // Unit price: 60 base + 15 whipped cream = 75
      expect(cartProvider.items[0].unitPrice, 75.0);
      expect(cartProvider.items[0].totalSubtotal, 75.0);
      expect(cartProvider.items[0].notes, 'Extra hot');
    });

    test('Adding identical product with same options and notes should increment quantity', () {
      cartProvider.addToCart(testProduct1, 1, [testOption1], 'No ice');
      cartProvider.addToCart(testProduct1, 2, [testOption1], 'No ice');

      expect(cartProvider.items.length, 1);
      expect(cartProvider.items[0].quantity, 3);
    });

    test('Adding same product with DIFFERENT options or notes should add a new line item', () {
      cartProvider.addToCart(testProduct1, 1, [testOption1], 'No ice');
      // Different options
      cartProvider.addToCart(testProduct1, 1, [testOption2], 'No ice');
      // Different notes
      cartProvider.addToCart(testProduct1, 1, [testOption1], 'Extra ice');

      expect(cartProvider.items.length, 3);
    });

    test('Updating quantities should modify cart correctly', () {
      cartProvider.addToCart(testProduct2, 2, [], null);
      cartProvider.updateQuantity(0, 5);

      expect(cartProvider.items[0].quantity, 5);

      // Updating quantity to 0 or less should remove item
      cartProvider.updateQuantity(0, 0);
      expect(cartProvider.items.isEmpty, true);
    });

    test('Removing from cart should delete correct index', () {
      cartProvider.addToCart(testProduct1, 1, [], null);
      cartProvider.addToCart(testProduct2, 1, [], null);

      expect(cartProvider.items.length, 2);
      cartProvider.removeFromCart(0);

      expect(cartProvider.items.length, 1);
      expect(cartProvider.items[0].product.id, 'p2');
    });

    test('Clearing cart should reset everything', () {
      cartProvider.setTable('table123', 'A1');
      cartProvider.addToCart(testProduct1, 2, [], null);

      expect(cartProvider.items.length, 1);
      expect(cartProvider.selectedTableId, 'table123');

      cartProvider.clearCart();

      expect(cartProvider.items.isEmpty, true);
      expect(cartProvider.selectedTableId, null);
      expect(cartProvider.selectedTableNumber, null);
    });
  });
}
