import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  bool _isAuthenticated = false;
  String? _token;
  String? _username;
  String? _name;
  String? _role;
  bool _isLoading = false;

  bool get isAuthenticated => _isAuthenticated;
  String? get token => _token;
  String? get username => _username;
  String? get name => _name;
  String? get role => _role;
  bool get isLoading => _isLoading;

  // Try auto login using persisted token
  Future<bool> tryAutoLogin() async {
    await ApiService.init();
    final savedToken = ApiService.token;
    if (savedToken == null) return false;

    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.get('/auth/me');
      final data = jsonDecode(response.body);
      
      _isAuthenticated = true;
      _token = savedToken;
      _username = data['username'];
      _name = data['name'];
      _role = data['role'];
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      // Token invalid or network error
      await ApiService.clearToken();
      _isAuthenticated = false;
      _token = null;
      _username = null;
      _name = null;
      _role = null;
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  // Login via API
  Future<void> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.post('/auth/login', {
        'username': username,
        'password': password,
      });

      final data = jsonDecode(response.body);
      _token = data['token'];
      _username = data['user']['username'];
      _name = data['user']['name'];
      _role = data['user']['role'];
      _isAuthenticated = true;

      await ApiService.saveToken(_token!);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Logout
  Future<void> logout() async {
    _isAuthenticated = false;
    _token = null;
    _username = null;
    _name = null;
    _role = null;
    await ApiService.clearToken();
    notifyListeners();
  }
}
