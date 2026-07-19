import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/table_model.dart';
import '../services/api_service.dart';

class TableProvider extends ChangeNotifier {
  List<TableModel> _tables = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<TableModel> get tables => _tables;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchTables() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await ApiService.get('/tables');
      final List<dynamic> decoded = jsonDecode(response.body);
      _tables = decoded.map((json) => TableModel.fromJson(json)).toList();
    } catch (e) {
      _errorMessage = 'Failed to load tables: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Update local table status (optimistic or after API call)
  Future<void> updateTableStatus(String tableId, String status) async {
    try {
      final tableIndex = _tables.indexWhere((t) => t.id == tableId);
      if (tableIndex == -1) return;

      final currentTable = _tables[tableIndex];
      final response = await ApiService.put('/tables/$tableId', {
        'number': currentTable.number,
        'status': status,
      });

      final updatedJson = jsonDecode(response.body);
      _tables[tableIndex] = TableModel.fromJson(updatedJson);
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to update table: $e';
      notifyListeners();
    }
  }
}
