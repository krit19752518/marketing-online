import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class TablesManagementScreen extends StatefulWidget {
  const TablesManagementScreen({super.key});

  @override
  State<TablesManagementScreen> createState() => _TablesManagementScreenState();
}

class _TablesManagementScreenState extends State<TablesManagementScreen> {
  List<dynamic> _tables = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchTables();
  }

  Future<void> _fetchTables() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await ApiService.get('/tables');
      setState(() {
        _tables = jsonDecode(response.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load tables: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _addTable(String number, int seats) async {
    try {
      await ApiService.post('/tables', {
        'number': number,
        'seats': seats,
      });
      _fetchTables();
    } catch (e) {
      _showSnackBar('Failed to add table: $e', Colors.red);
    }
  }

  Future<void> _editTable(String id, String number, int seats) async {
    try {
      await ApiService.put('/tables/$id', {
        'number': number,
        'seats': seats,
      });
      _fetchTables();
    } catch (e) {
      _showSnackBar('Failed to update table: $e', Colors.red);
    }
  }

  Future<void> _deleteTable(String id) async {
    try {
      await ApiService.delete('/tables/$id');
      _fetchTables();
    } catch (e) {
      _showSnackBar('Failed to delete table: $e', Colors.red);
    }
  }

  void _showSnackBar(String msg, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: color),
    );
  }

  void _openTableDialog({Map<String, dynamic>? table}) {
    final isEdit = table != null;
    final numberController = TextEditingController(text: isEdit ? table['number'] : '');
    final seatsController = TextEditingController(text: isEdit ? table['seats'].toString() : '4');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Table Settings' : 'Add New Table'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: numberController,
              decoration: const InputDecoration(
                labelText: 'Table Number / Name (เลขที่โต๊ะ)',
                hintText: 'e.g. A1, B4, VIP2',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: seatsController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Seat Capacity (จำนวนเก้าอี้)',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final number = numberController.text.trim();
              final seats = int.tryParse(seatsController.text) ?? 4;
              if (number.isNotEmpty) {
                if (isEdit) {
                  _editTable(table['id'], number, seats);
                } else {
                  _addTable(number, seats);
                }
                Navigator.pop(context);
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
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
          _sidebarItem(context, Icons.table_restaurant_rounded, 'Tables', '/tables', true),
          _sidebarItem(context, Icons.inventory_2_rounded, 'Inventory', '/inventory', false),
          _sidebarItem(context, Icons.badge_rounded, 'Employees', '/employees', false),
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

  Color _getStatusColor(String status) {
    switch (status) {
      case 'VACANT':
        return Colors.teal;
      case 'OCCUPIED':
        return Colors.orange.shade800;
      case 'BILLING':
        return Colors.amber.shade700;
      default:
        return Colors.grey;
    }
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
                            ElevatedButton(onPressed: _fetchTables, child: const Text('Retry')),
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
                                      'Table Configuration',
                                      style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Manage physical layout, seat capacities, and status updates',
                                      style: theme.textTheme.bodyMedium?.copyWith(
                                        color: theme.colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.add_circle_outline_rounded),
                                  label: const Text('Add Table'),
                                  onPressed: () => _openTableDialog(),
                                ),
                              ],
                            ),
                            const SizedBox(height: 32),

                            // Tables Grid
                            Expanded(
                              child: _tables.isEmpty
                                  ? Center(
                                      child: Text(
                                        'No tables configured yet.',
                                        style: theme.textTheme.bodyLarge?.copyWith(
                                          color: theme.colorScheme.onSurfaceVariant,
                                        ),
                                      ),
                                    )
                                  : GridView.builder(
                                      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                                        maxCrossAxisExtent: 220,
                                        crossAxisSpacing: 20,
                                        mainAxisSpacing: 20,
                                        childAspectRatio: 1.1,
                                      ),
                                      itemCount: _tables.length,
                                      itemBuilder: (context, index) {
                                        final table = _tables[index];
                                        final status = table['status'] as String;
                                        final statusColor = _getStatusColor(status);

                                        return Card(
                                          elevation: 2,
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(16),
                                            side: BorderSide(
                                              color: statusColor.withValues(alpha: 0.5),
                                              width: 1.5,
                                            ),
                                          ),
                                          child: Padding(
                                            padding: const EdgeInsets.all(16.0),
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Row(
                                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                                  children: [
                                                    Text(
                                                      'Table ${table['number']}',
                                                      style: const TextStyle(
                                                        fontWeight: FontWeight.bold,
                                                        fontSize: 16,
                                                      ),
                                                    ),
                                                    Container(
                                                      padding: const EdgeInsets.symmetric(
                                                        horizontal: 8,
                                                        vertical: 4,
                                                      ),
                                                      decoration: BoxDecoration(
                                                        color: statusColor.withValues(alpha: 0.1),
                                                        borderRadius: BorderRadius.circular(8),
                                                      ),
                                                      child: Text(
                                                        status,
                                                        style: TextStyle(
                                                          color: statusColor,
                                                          fontWeight: FontWeight.bold,
                                                          fontSize: 10,
                                                        ),
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                                const SizedBox(height: 8),
                                                Text(
                                                  'Seats: ${table['seats']} chairs',
                                                  style: theme.textTheme.bodyMedium?.copyWith(
                                                    color: theme.colorScheme.onSurfaceVariant,
                                                  ),
                                                ),
                                                const Spacer(),
                                                Row(
                                                  mainAxisAlignment: MainAxisAlignment.end,
                                                  children: [
                                                    IconButton(
                                                      icon: const Icon(Icons.edit_rounded, color: Colors.blue),
                                                      onPressed: () => _openTableDialog(table: table),
                                                    ),
                                                    IconButton(
                                                      icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                                                      onPressed: () {
                                                        showDialog(
                                                          context: context,
                                                          builder: (context) => AlertDialog(
                                                            title: const Text('Delete Table?'),
                                                            content: const Text(
                                                              'Are you sure you want to delete this table? This cannot be undone.',
                                                            ),
                                                            actions: [
                                                              TextButton(
                                                                onPressed: () => Navigator.pop(context),
                                                                child: const Text('Cancel'),
                                                              ),
                                                              TextButton(
                                                                onPressed: () {
                                                                  _deleteTable(table['id']);
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
                                              ],
                                            ),
                                          ),
                                        );
                                      },
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
