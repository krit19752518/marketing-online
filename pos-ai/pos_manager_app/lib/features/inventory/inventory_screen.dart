import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  List<dynamic> _inventory = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchInventory();
  }

  Future<void> _fetchInventory() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await ApiService.get('/inventory');
      setState(() {
        _inventory = jsonDecode(response.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load inventory: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveInventoryItem({
    String? id,
    required String name,
    required double quantity,
    required String unit,
    required double minStock,
  }) async {
    final payload = {
      'name': name,
      'quantity': quantity,
      'unit': unit,
      'minStock': minStock,
    };

    try {
      if (id == null) {
        await ApiService.post('/inventory', payload);
      } else {
        await ApiService.put('/inventory/$id', payload);
      }
      _fetchInventory();
    } catch (e) {
      _showSnackBar('Failed to save inventory item: $e', Colors.red);
    }
  }

  Future<void> _adjustQuantity(String id, double delta) async {
    try {
      final item = _inventory.firstWhere((i) => i['id'] == id);
      final double newQty = (item['quantity'] as num).toDouble() + delta;

      await ApiService.put('/inventory/$id', {
        'name': item['name'],
        'unit': item['unit'],
        'minStock': (item['minStock'] as num).toDouble(),
        'quantity': newQty < 0 ? 0.0 : newQty,
      });
      _fetchInventory();
    } catch (e) {
      _showSnackBar('Failed to adjust stock: $e', Colors.red);
    }
  }

  Future<void> _deleteItem(String id) async {
    try {
      await ApiService.delete('/inventory/$id');
      _fetchInventory();
    } catch (e) {
      _showSnackBar('Failed to delete item: $e', Colors.red);
    }
  }

  void _showSnackBar(String msg, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: color),
    );
  }

  void _openItemDialog({Map<String, dynamic>? item}) {
    final isEdit = item != null;
    final nameController = TextEditingController(text: isEdit ? item['name'] : '');
    final qtyController = TextEditingController(text: isEdit ? item['quantity'].toString() : '0');
    final unitController = TextEditingController(text: isEdit ? item['unit'] : 'kg');
    final minStockController = TextEditingController(text: isEdit ? item['minStock'].toString() : '5');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Inventory Item' : 'Add New Inventory Item'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: 'Item Name (ชื่อวัตถุดิบ/สินค้า)',
                hintText: 'e.g. Fresh Milk, Coffee Beans, Syrup',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: qtyController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Quantity (จำนวนในคลัง)',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: unitController,
              decoration: const InputDecoration(
                labelText: 'Unit (หน่วยนับ)',
                hintText: 'e.g. kg, pcs, bags, litres',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: minStockController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Min Stock Level (จุดเตือนของหมด)',
                hintText: 'Alert displays if quantity goes below this level',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final name = nameController.text.trim();
              final qty = double.tryParse(qtyController.text) ?? 0.0;
              final unit = unitController.text.trim();
              final min = double.tryParse(minStockController.text) ?? 5.0;

              if (name.isNotEmpty && unit.isNotEmpty) {
                _saveInventoryItem(
                  id: isEdit ? item['id'] : null,
                  name: name,
                  quantity: qty,
                  unit: unit,
                  minStock: min,
                );
                Navigator.pop(context);
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _openQuickAdjustDialog(Map<String, dynamic> item) {
    final qtyController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Adjust Stock: ${item['name']}'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Current Stock: ${item['quantity']} ${item['unit']}'),
            const SizedBox(height: 16),
            TextField(
              controller: qtyController,
              keyboardType: const TextInputType.numberWithOptions(signed: true, decimal: true),
              decoration: const InputDecoration(
                labelText: 'Adjust Value (+ to add, - to subtract)',
                hintText: 'e.g. +10, -5',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final delta = double.tryParse(qtyController.text) ?? 0.0;
              if (delta != 0.0) {
                _adjustQuantity(item['id'], delta);
              }
              Navigator.pop(context);
            },
            child: const Text('Confirm'),
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
          _sidebarItem(context, Icons.table_restaurant_rounded, 'Tables', '/tables', false),
          _sidebarItem(context, Icons.inventory_2_rounded, 'Inventory', '/inventory', true),
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
                            ElevatedButton(onPressed: _fetchInventory, child: const Text('Retry')),
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
                                      'Inventory Management',
                                      style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Monitor stock levels, highlight shortages, and log inventory restocks',
                                      style: theme.textTheme.bodyMedium?.copyWith(
                                        color: theme.colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                                ElevatedButton.icon(
                                  icon: const Icon(Icons.add_box_rounded),
                                  label: const Text('Add Stock Item'),
                                  onPressed: () => _openItemDialog(),
                                ),
                              ],
                            ),
                            const SizedBox(height: 32),

                            // Inventory Table List
                            Expanded(
                              child: _inventory.isEmpty
                                  ? Center(
                                      child: Text(
                                        'No inventory items configured.',
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
                                        itemCount: _inventory.length,
                                        separatorBuilder: (context, index) => const Divider(),
                                        itemBuilder: (context, index) {
                                          final item = _inventory[index];
                                          final qty = (item['quantity'] as num).toDouble();
                                          final min = (item['minStock'] as num).toDouble();
                                          final isLow = qty <= min;

                                          return ListTile(
                                            contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                                            title: Row(
                                              children: [
                                                Text(
                                                  item['name'],
                                                  style: const TextStyle(fontWeight: FontWeight.bold),
                                                ),
                                                const SizedBox(width: 12),
                                                if (isLow)
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(
                                                      horizontal: 8,
                                                      vertical: 2,
                                                    ),
                                                    decoration: BoxDecoration(
                                                      color: Colors.red.shade50,
                                                      borderRadius: BorderRadius.circular(6),
                                                    ),
                                                    child: Text(
                                                      'LOW STOCK',
                                                      style: TextStyle(
                                                        color: Colors.red.shade800,
                                                        fontWeight: FontWeight.bold,
                                                        fontSize: 10,
                                                      ),
                                                    ),
                                                  ),
                                              ],
                                            ),
                                            subtitle: Text('Min stock limit: $min ${item['unit']}'),
                                            trailing: Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                Text(
                                                  '$qty ${item['unit']}',
                                                  style: TextStyle(
                                                    fontWeight: FontWeight.bold,
                                                    fontSize: 16,
                                                    color: isLow ? Colors.red.shade800 : Colors.teal.shade800,
                                                  ),
                                                ),
                                                const SizedBox(width: 24),
                                                ElevatedButton(
                                                  style: ElevatedButton.styleFrom(
                                                    backgroundColor: Colors.teal.shade50,
                                                    foregroundColor: Colors.teal.shade900,
                                                    elevation: 0,
                                                  ),
                                                  onPressed: () => _openQuickAdjustDialog(item),
                                                  child: const Text('Adjust'),
                                                ),
                                                const SizedBox(width: 8),
                                                IconButton(
                                                  icon: const Icon(Icons.edit_rounded, color: Colors.blue),
                                                  onPressed: () => _openItemDialog(item: item),
                                                ),
                                                IconButton(
                                                  icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                                                  onPressed: () {
                                                    showDialog(
                                                      context: context,
                                                      builder: (context) => AlertDialog(
                                                        title: const Text('Delete Stock Item?'),
                                                        content: const Text(
                                                          'Are you sure you want to delete this stock item? This cannot be undone.',
                                                        ),
                                                        actions: [
                                                          TextButton(
                                                            onPressed: () => Navigator.pop(context),
                                                            child: const Text('Cancel'),
                                                          ),
                                                          TextButton(
                                                            onPressed: () {
                                                              _deleteItem(item['id']);
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
