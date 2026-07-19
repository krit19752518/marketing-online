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

  Future<bool> tryAutoLogin() async {
    await ApiService.init();
    final savedToken = ApiService.token;
    if (savedToken == null) return false;

    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.get('/auth/me');
      final data = jsonDecode(response.body);

      // Verify that the user has Owner or Manager privileges to access manager app
      final userRole = data['role'] as String;
      if (userRole != 'OWNER' && userRole != 'MANAGER') {
        throw Exception('Access restricted to owners and managers only');
      }

      _isAuthenticated = true;
      _token = savedToken;
      _username = data['username'];
      _name = data['name'];
      _role = userRole;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
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

  Future<void> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.post('/auth/login', {
        'username': username,
        'password': password,
      });

      final data = jsonDecode(response.body);
      final userRole = data['user']['role'] as String;

      if (userRole != 'OWNER' && userRole != 'MANAGER') {
        throw ApiException('Access restricted to owners and managers only', 403);
      }

      _token = data['token'];
      _username = data['user']['username'];
      _name = data['user']['name'];
      _role = userRole;
      _isAuthenticated = true;

      await ApiService.saveToken(_token!);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

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
