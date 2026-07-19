import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class MenuManagementScreen extends StatefulWidget {
  const MenuManagementScreen({super.key});

  @override
  State<MenuManagementScreen> createState() => _MenuManagementScreenState();
}

class _MenuManagementScreenState extends State<MenuManagementScreen> with SingleTickerProviderStateMixin {
  TabController? _tabController;
  List<dynamic> _categories = [];
  List<dynamic> _products = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchData();
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final catResponse = await ApiService.get('/categories');
      final prodResponse = await ApiService.get('/products');

      setState(() {
        _categories = jsonDecode(catResponse.body);
        _products = jsonDecode(prodResponse.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load menu data: $e';
        _isLoading = false;
      });
    }
  }

  // --- Category CRUD Actions ---
  Future<void> _addCategory(String name) async {
    try {
      await ApiService.post('/categories', {'name': name});
      _fetchData();
    } catch (e) {
      _showSnackBar('Failed to add category: $e', Colors.red);
    }
  }

  Future<void> _editCategory(String id, String name) async {
    try {
      await ApiService.put('/categories/$id', {'name': name});
      _fetchData();
    } catch (e) {
      _showSnackBar('Failed to update category: $e', Colors.red);
    }
  }

  Future<void> _deleteCategory(String id) async {
    try {
      await ApiService.delete('/categories/$id');
      _fetchData();
    } catch (e) {
      _showSnackBar('Failed to delete category: $e', Colors.red);
    }
  }

  // --- Product CRUD Actions ---
  Future<void> _saveProduct({
    String? id,
    required String name,
    required double price,
    required String categoryId,
    String? description,
    String? imageUrl,
    required String status,
    required List<Map<String, dynamic>> options,
  }) async {
    final payload = {
      'name': name,
      'price': price,
      'categoryId': categoryId,
      'description': description,
      'imageUrl': imageUrl,
      'status': status,
      'options': options,
    };

    try {
      if (id == null) {
        await ApiService.post('/products', payload);
      } else {
        await ApiService.put('/products/$id', payload);
      }
      _fetchData();
    } catch (e) {
      _showSnackBar('Failed to save product: $e', Colors.red);
    }
  }

  Future<void> _deleteProduct(String id) async {
    try {
      await ApiService.delete('/products/$id');
      _fetchData();
    } catch (e) {
      _showSnackBar('Failed to delete product: $e', Colors.red);
    }
  }

  void _showSnackBar(String msg, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: color),
    );
  }

  // --- UI dialogs ---
  void _openCategoryDialog({String? id, String? currentName}) {
    final controller = TextEditingController(text: currentName);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(id == null ? 'Add Category' : 'Edit Category'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(labelText: 'Category Name'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                if (id == null) {
                  _addCategory(name);
                } else {
                  _editCategory(id, name);
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

  void _openProductDialog({Map<String, dynamic>? product}) {
    final isEdit = product != null;
    final nameController = TextEditingController(text: isEdit ? product['name'] : '');
    final priceController = TextEditingController(text: isEdit ? product['price'].toString() : '');
    final descController = TextEditingController(text: isEdit ? product['description'] : '');
    final imgController = TextEditingController(text: isEdit ? product['imageUrl'] : '');
    String selectedCatId = isEdit ? product['categoryId'] : (_categories.isNotEmpty ? _categories[0]['id'] : '');
    String selectedStatus = isEdit ? product['status'] : 'AVAILABLE';

    // Parse options
    List<Map<String, dynamic>> rawOptions = [];
    if (isEdit && product['options'] != null) {
      for (var o in product['options']) {
        rawOptions.add({
          'id': o['id'] ?? '',
          'name': o['name'] ?? '',
          'price': (o['price'] as num).toDouble(),
        });
      }
    }

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return AlertDialog(
              title: Text(isEdit ? 'Edit Product' : 'Add New Product'),
              content: SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 450),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextField(
                        controller: nameController,
                        decoration: const InputDecoration(labelText: 'Product Name (ชื่อสินค้า)'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: priceController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Price (฿ ราคา)'),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: selectedCatId.isEmpty ? null : selectedCatId,
                        decoration: const InputDecoration(labelText: 'Category'),
                        items: _categories.map<DropdownMenuItem<String>>((c) {
                          return DropdownMenuItem<String>(value: c['id'], child: Text(c['name']));
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() => selectedCatId = val);
                          }
                        },
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: selectedStatus,
                        decoration: const InputDecoration(labelText: 'Status'),
                        items: const [
                          DropdownMenuItem(value: 'AVAILABLE', child: Text('Available')),
                          DropdownMenuItem(value: 'OUT_OF_STOCK', child: Text('Out of Stock')),
                        ],
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() => selectedStatus = val);
                          }
                        },
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: descController,
                        decoration: const InputDecoration(labelText: 'Description (คำอธิบาย)'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: imgController,
                        decoration: const InputDecoration(labelText: 'Image URL'),
                      ),
                      const Divider(height: 32),

                      // Options Customizer Section
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Options (ตัวเลือกเพิ่มเติม)', style: TextStyle(fontWeight: FontWeight.bold)),
                          IconButton(
                            icon: const Icon(Icons.add_circle_outline_rounded, color: Colors.blue),
                            onPressed: () {
                              setModalState(() {
                                rawOptions.add({'name': 'New Option', 'price': 0.0});
                              });
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ...List.generate(rawOptions.length, (index) {
                        final opt = rawOptions[index];
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4.0),
                          child: Row(
                            children: [
                              Expanded(
                                flex: 3,
                                child: TextFormField(
                                  initialValue: opt['name'],
                                  decoration: const InputDecoration(hintText: 'Option name'),
                                  onChanged: (val) => opt['name'] = val,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                flex: 2,
                                child: TextFormField(
                                  initialValue: opt['price'].toString(),
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(hintText: '+฿ Price'),
                                  onChanged: (val) => opt['price'] = double.tryParse(val) ?? 0.0,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete_outline, color: Colors.red),
                                onPressed: () {
                                  setModalState(() {
                                    rawOptions.removeAt(index);
                                  });
                                },
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                ElevatedButton(
                  onPressed: () {
                    final price = double.tryParse(priceController.text) ?? 0.0;
                    if (nameController.text.trim().isNotEmpty && selectedCatId.isNotEmpty) {
                      _saveProduct(
                        id: isEdit ? product['id'] : null,
                        name: nameController.text.trim(),
                        price: price,
                        categoryId: selectedCatId,
                        description: descController.text.trim(),
                        imageUrl: imgController.text.trim(),
                        status: selectedStatus,
                        options: rawOptions,
                      );
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
          _sidebarItem(context, Icons.restaurant_menu_rounded, 'Menu Items', '/menu', true),
          _sidebarItem(context, Icons.table_restaurant_rounded, 'Tables', '/tables', false),
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
                            ElevatedButton(onPressed: _fetchData, child: const Text('Retry')),
                          ],
                        ),
                      )
                    : Padding(
                        padding: const EdgeInsets.all(32.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Menu & Category Management',
                                  style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                                ),
                                TabBar(
                                  controller: _tabController,
                                  isScrollable: true,
                                  tabs: const [
                                    Tab(text: 'Products (รายการสินค้า)'),
                                    Tab(text: 'Categories (หมวดหมู่สินค้า)'),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 24),
                            Expanded(
                              child: TabBarView(
                                controller: _tabController,
                                children: [
                                  // 1. Products CRUD View
                                  _buildProductsTab(theme),

                                  // 2. Categories CRUD View
                                  _buildCategoriesTab(theme),
                                ],
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

  Widget _buildProductsTab(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('All Products', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            ElevatedButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Add Product'),
              onPressed: () => _openProductDialog(),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Expanded(
          child: ListView.separated(
            itemCount: _products.length,
            separatorBuilder: (context, index) => const Divider(),
            itemBuilder: (context, index) {
              final prod = _products[index];
              final cat = _categories.firstWhere((c) => c['id'] == prod['categoryId'], orElse: () => {'name': 'Unknown'});
              final status = prod['status'] as String;

              return ListTile(
                title: Text(prod['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Category: ${cat['name']} • Price: ฿${prod['price'].toString()}'),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: status == 'AVAILABLE' ? Colors.green.shade50 : Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        status,
                        style: TextStyle(
                          color: status == 'AVAILABLE' ? Colors.green.shade800 : Colors.red.shade800,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: const Icon(Icons.edit_rounded, color: Colors.blue),
                      onPressed: () => _openProductDialog(product: prod),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Delete Product?'),
                            content: const Text('Are you sure you want to delete this product?'),
                            actions: [
                              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                              TextButton(
                                onPressed: () {
                                  _deleteProduct(prod['id']);
                                  Navigator.pop(context);
                                },
                                child: const Text('Delete', style: TextStyle(color: Colors.red)),
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
      ],
    );
  }

  Widget _buildCategoriesTab(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('All Categories', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            ElevatedButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Add Category'),
              onPressed: () => _openCategoryDialog(),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Expanded(
          child: ListView.separated(
            itemCount: _categories.length,
            separatorBuilder: (context, index) => const Divider(),
            itemBuilder: (context, index) {
              final cat = _categories[index];
              return ListTile(
                title: Text(cat['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.edit_rounded, color: Colors.blue),
                      onPressed: () => _openCategoryDialog(id: cat['id'], currentName: cat['name']),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Delete Category?'),
                            content: const Text('Deleting this category may affect linked products. Continue?'),
                            actions: [
                              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                              TextButton(
                                onPressed: () {
                                  _deleteCategory(cat['id']);
                                  Navigator.pop(context);
                                },
                                child: const Text('Delete', style: TextStyle(color: Colors.red)),
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
      ],
    );
  }
}
