import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  String? _token;
  String? _name;
  String? _role;
  String? _tenantId;
  String? _tenantName;

  bool _isLoading = false;

  String? get token => _token;
  String? get name => _name;
  String? get role => _role;
  String? get tenantId => _tenantId;
  String? get tenantName => _tenantName;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;

  Future<void> tryAutoLogin() async {
    final savedToken = await ApiService.getToken();
    if (savedToken != null) {
      // Decode JWT token payload
      try {
        final parts = savedToken.split('.');
        if (parts.length == 3) {
          final payloadStr = utf8.decode(base64Url.decode(base64Url.normalize(parts[1])));
          final payload = jsonDecode(payloadStr);
          
          _token = savedToken;
          _name = payload['name'];
          _role = payload['role'];
          _tenantId = payload['tenant_id'];
          // Default tenant name if auto-login is from payload
          _tenantName = "My Store";
          notifyListeners();
        }
      } catch (e) {
        await logout();
      }
    }
  }

  Future<bool> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.post('/auth/login', {
        'username': username,
        'password': password,
      });

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['token'];
        _name = data['name'];
        _role = data['role'];
        _tenantId = data['tenant_id'];
        _tenantName = data['tenant_name'];
        
        await ApiService.saveToken(_token!);
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _token = null;
    _name = null;
    _role = null;
    _tenantId = null;
    _tenantName = null;
    await ApiService.clearToken();
    notifyListeners();
  }
}
