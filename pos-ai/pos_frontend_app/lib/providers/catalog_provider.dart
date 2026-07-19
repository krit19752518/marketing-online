import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/category_model.dart';
import '../models/product_model.dart';
import '../services/api_service.dart';

class CatalogProvider extends ChangeNotifier {
  List<CategoryModel> _categories = [];
  List<ProductModel> _products = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<CategoryModel> get categories => _categories;
  List<ProductModel> get products => _products;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchCatalog() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // 1. Fetch categories
      final catResponse = await ApiService.get('/categories');
      final List<dynamic> catDecoded = jsonDecode(catResponse.body);
      _categories = catDecoded.map((json) => CategoryModel.fromJson(json)).toList();

      // 2. Fetch products
      final prodResponse = await ApiService.get('/products');
      final List<dynamic> prodDecoded = jsonDecode(prodResponse.body);
      _products = prodDecoded.map((json) => ProductModel.fromJson(json)).toList();
    } catch (e) {
      _errorMessage = 'Failed to load catalog: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Helper to get products belonging to a category
  List<ProductModel> getProductsByCategory(String categoryId) {
    return _products.where((p) => p.categoryId == categoryId).toList();
  }
}
