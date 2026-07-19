import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/cart_item_model.dart';
import '../models/product_model.dart';
import '../services/api_service.dart';

class CartProvider extends ChangeNotifier {
  final List<CartItemModel> _items = [];
  String? _selectedTableId;
  String? _selectedTableNumber;
  bool _isSubmitting = false;

  List<CartItemModel> get items => _items;
  String? get selectedTableId => _selectedTableId;
  String? get selectedTableNumber => _selectedTableNumber;
  bool get isSubmitting => _isSubmitting;

  void setTable(String? tableId, String? tableNumber) {
    _selectedTableId = tableId;
    _selectedTableNumber = tableNumber;
    notifyListeners();
  }

  void addToCart(ProductModel product, int quantity, List<ProductOptionModel> selectedOptions, String? notes) {
    // Check if identical item (same product & same options & same notes) already exists
    int existingIndex = _items.indexWhere((item) {
      if (item.product.id != product.id) return false;
      if (item.notes != notes) return false;
      if (item.selectedOptions.length != selectedOptions.length) return false;
      
      // Compare option ids
      final existingOptIds = item.selectedOptions.map((o) => o.id).toSet();
      final newOptIds = selectedOptions.map((o) => o.id).toSet();
      return existingOptIds.difference(newOptIds).isEmpty;
    });

    if (existingIndex != -1) {
      _items[existingIndex].quantity += quantity;
    } else {
      _items.add(
        CartItemModel(
          product: product,
          quantity: quantity,
          selectedOptions: selectedOptions,
          notes: notes,
        ),
      );
    }
    notifyListeners();
  }

  void updateQuantity(int index, int quantity) {
    if (index >= 0 && index < _items.length) {
      _items[index].quantity = quantity;
      if (_items[index].quantity <= 0) {
        _items.removeAt(index);
      }
      notifyListeners();
    }
  }

  void removeFromCart(int index) {
    if (index >= 0 && index < _items.length) {
      _items.removeAt(index);
      notifyListeners();
    }
  }

  void clearCart() {
    _items.clear();
    _selectedTableId = null;
    _selectedTableNumber = null;
    _isSubmitting = false;
    notifyListeners();
  }

  double get subtotalAmount {
    return _items.fold(0.0, (sum, item) => sum + item.totalSubtotal);
  }

  double get vatAmount {
    return subtotalAmount * 0.07; // 7% VAT
  }

  double get totalAmount {
    return subtotalAmount + vatAmount;
  }

  // Submit cart items to backend to create an order
  Future<String> submitOrder() async {
    _isSubmitting = true;
    notifyListeners();

    try {
      final payload = {
        if (_selectedTableId != null) 'tableId': _selectedTableId,
        'items': _items.map((item) => {
          'productId': item.product.id,
          'quantity': item.quantity,
          if (item.notes != null) 'notes': item.notes,
          'selectedOpts': item.selectedOptions.map((opt) => {
            'name': opt.name,
            'price': opt.price,
          }).toList(),
        }).toList(),
      };

      final response = await ApiService.post('/orders', payload);
      final data = jsonDecode(response.body);
      return data['id'] as String;
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }
}
