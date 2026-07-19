import 'product_model.dart';

class CartItemModel {
  final ProductModel product;
  int quantity;
  final List<ProductOptionModel> selectedOptions;
  String? notes;

  CartItemModel({
    required this.product,
    this.quantity = 1,
    required this.selectedOptions,
    this.notes,
  });

  double get unitPrice {
    double optionsPrice = selectedOptions.fold(0.0, (sum, opt) => sum + opt.price);
    return product.price + optionsPrice;
  }

  double get totalSubtotal {
    return unitPrice * quantity;
  }
}
