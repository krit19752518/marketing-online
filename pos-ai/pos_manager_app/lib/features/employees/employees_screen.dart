import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class EmployeesScreen extends StatefulWidget {
  const EmployeesScreen({super.key});

  @override
  State<EmployeesScreen> createState() => _EmployeesScreenState();
}

class _EmployeesScreenState extends State<EmployeesScreen> {
  List<dynamic> _employees = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchEmployees();
  }

  Future<void> _fetchEmployees() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await ApiService.get('/auth/users');
      setState(() {
        _employees = jsonDecode(response.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load employees: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _addEmployee(String username, String password, String name, String role) async {
    try {
      await ApiService.post('/auth/register', {
        'username': username,
        'password': password,
        'name': name,
        'role': role,
      });
      _fetchEmployees();
    } catch (e) {
      _showSnackBar('Failed to register employee: $e', Colors.red);
    }
  }

  Future<void> _editEmployee(String id, String name, String role, String? password) async {
    try {
      await ApiService.put('/auth/users/$id', {
        'name': name,
        'role': role,
        if (password != null && password.trim().isNotEmpty) 'password': password,
      });
      _fetchEmployees();
    } catch (e) {
      _showSnackBar('Failed to update employee: $e', Colors.red);
    }
  }

  Future<void> _deleteEmployee(String id) async {
    try {
      await ApiService.delete('/auth/users/$id');
      _fetchEmployees();
    } catch (e) {
      _showSnackBar('Failed to delete employee: $e', Colors.red);
    }
  }

  void _showSnackBar(String msg, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: color),
    );
  }

  void _openEmployeeDialog({Map<String, dynamic>? employee}) {
    final isEdit = employee != null;
    final usernameController = TextEditingController(text: isEdit ? employee['username'] : '');
    final passwordController = TextEditingController();
    final nameController = TextEditingController(text: isEdit ? employee['name'] : '');
    String selectedRole = isEdit ? employee['role'] : 'STAFF';

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return AlertDialog(
              title: Text(isEdit ? 'Edit Employee Details' : 'Register New Employee'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!isEdit)
                    TextField(
                      controller: usernameController,
                      decoration: const InputDecoration(labelText: 'Username (ชื่อใช้เข้าสู่ระบบ)'),
                    ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(labelText: 'Full Name (ชื่อ-นามสกุลพนักงาน)'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: passwordController,
                    obscureText: true,
                    decoration: InputDecoration(
                      labelText: isEdit ? 'New Password (เว้นว่างไว้เพื่อไม่เปลี่ยน)' : 'Password (รหัสผ่าน)',
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: selectedRole,
                    decoration: const InputDecoration(labelText: 'Role / Position'),
                    items: const [
                      DropdownMenuItem(value: 'OWNER', child: Text('Owner (เจ้าของร้าน)')),
                      DropdownMenuItem(value: 'MANAGER', child: Text('Manager (ผู้จัดการร้าน)')),
                      DropdownMenuItem(value: 'CASHIER', child: Text('Cashier (พนักงานคิดเงิน)')),
                      DropdownMenuItem(value: 'STAFF', child: Text('Staff (พนักงานทั่วไป)')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setModalState(() => selectedRole = val);
                      }
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                ElevatedButton(
                  onPressed: () {
                    final name = nameController.text.trim();
                    final username = usernameController.text.trim();
                    final password = passwordController.text.trim();

                    if (name.isNotEmpty) {
                      if (isEdit) {
                        _editEmployee(
                          employee['id'],
                          name,
                          selectedRole,
                          password.isEmpty ? null : password,
                        );
                      } else {
                        if (username.isNotEmpty && password.isNotEmpty) {
                          _addEmployee(username, password, name, selectedRole);
                        }
                      }
                      Navigator.pop(context);
                    }
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildSidebar(BuildContext context) {
    final theme = Theme.of(context);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    return Container(
      width: 250,
      color: theme.colorScheme.surfaceContainerLow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.only(top: 48, bottom: 24, left: 24, right: 24),
            color: theme.colorScheme.primaryContainer.withValues(alpha: 0.15),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.analytics_rounded,
                      color: theme.colorScheme.primary,
                      size: 28,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'POS-AI Manager',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.primary,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'User: ${auth.name ?? 'Manager'}',
                  style: theme.textTheme.bodySmall,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _sidebarItem(context, Icons.dashboard_rounded, 'Dashboard', '/dashboard', false),
          _sidebarItem(context, Icons.restaurant_menu_rounded, 'Menu Items', '/menu', false),
          _sidebarItem(context, Icons.table_restaurant_rounded, 'Tables', '/tables', false),
          _sidebarItem(context, Icons.inventory_2_rounded, 'Inventory', '/inventory', false),
          _sidebarItem(context, Icons.badge_rounded, 'Employees', '/employees', true),
          const Spacer(),
          const Divider(),
          _sidebarItem(context, Icons.logout_rounded, 'Logout', '/login', false, isLogout: true),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _sidebarItem(BuildContext context, IconData icon, String label, String route, bool isSelected, {bool isLogout = false}) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
      child: Material(
        color: Colors.transparent,
        child: ListTile(
          leading: Icon(icon, color: isSelected ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant),
          title: Text(
            label,
            style: TextStyle(
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: isSelected ? theme.colorScheme.primary : theme.colorScheme.onSurface,
            ),
          ),
          selected: isSelected,
          selectedTileColor: theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          onTap: () async {
            if (isLogout) {
              await Provider.of<AuthProvider>(context, listen: false).logout();
              if (context.mounted) context.go(route);
            } else {
              context.go(route);
            }
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: Row(
        children: [
          _buildSidebar(context),
          const VerticalDivider(width: 1),

          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _errorMessage != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(_errorMessage!, style: TextStyle(color: theme.colorScheme.error)),
                            const SizedBox(height: 16),
                            ElevatedButton(onPressed: _fetchEmployees, child: const Text('Retry')),
                          ],
                        ),
                      )
                    : Padding(
                        padding: const EdgeInsets.all(32.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            // Page Header
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Employee Management',
                                      style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Manage staff member credentials, details, and access privileges',
                                      style: theme.textTheme.bodyMedium?.copyWith(
                                        color: theme.colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.person_add_alt_1_rounded),
                                  label: const Text('Add Employee'),
                                  onPressed: () => _openEmployeeDialog(),
                                ),
                              ],
                            ),
                            const SizedBox(height: 32),

                            // Employees Table
                            Expanded(
                              child: _employees.isEmpty
                                  ? Center(
                                      child: Text(
                                        'No employees registered.',
                                        style: theme.textTheme.bodyLarge?.copyWith(
                                          color: theme.colorScheme.onSurfaceVariant,
                                        ),
                                      ),
                                    )
                                  : Card(
                                      elevation: 1,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(16),
                                      ),
                                      child: ListView.separated(
                                        itemCount: _employees.length,
                                        separatorBuilder: (context, index) => const Divider(),
                                        itemBuilder: (context, index) {
                                          final emp = _employees[index];
                                          final role = emp['role'] as String;

                                          return ListTile(
                                            contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                                            leading: CircleAvatar(
                                              child: Text(
                                                emp['name'].substring(0, 1).toUpperCase(),
                                                style: const TextStyle(fontWeight: FontWeight.bold),
                                              ),
                                            ),
                                            title: Text(
                                              emp['name'],
                                              style: const TextStyle(fontWeight: FontWeight.bold),
                                            ),
                                            subtitle: Text('Username: ${emp['username']}'),
                                            trailing: Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                Chip(
                                                  label: Text(
                                                    role,
                                                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                                                  ),
                                                  backgroundColor: theme.colorScheme.secondaryContainer,
                                                ),
                                                const SizedBox(width: 16),
                                                IconButton(
                                                  icon: const Icon(Icons.edit_rounded, color: Colors.blue),
                                                  onPressed: () => _openEmployeeDialog(employee: emp),
                                                ),
                                                IconButton(
                                                  icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                                                  onPressed: () {
                                                    showDialog(
                                                      context: context,
                                                      builder: (context) => AlertDialog(
                                                        title: const Text('Delete Employee?'),
                                                        content: const Text(
                                                          'Are you sure you want to delete this employee? This will instantly revoke access.',
                                                        ),
                                                        actions: [
                                                          TextButton(
                                                            onPressed: () => Navigator.pop(context),
                                                            child: const Text('Cancel'),
                                                          ),
                                                          TextButton(
                                                            onPressed: () {
                                                              _deleteEmployee(emp['id']);
                                                              Navigator.pop(context);
                                                            },
                                                            child: const Text(
                                                              'Delete',
                                                              style: TextStyle(color: Colors.red),
                                                            ),
                                                          ),
                                                        ],
                                                      ),
                                                    );
                                                  },
                                                ),
                                              ],
                                            ),
                                          );
                                        },
                                      ),
                                    ),
                            ),
                          ],
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}
