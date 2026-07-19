import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../models/product_model.dart';
import '../../providers/catalog_provider.dart';
import '../../providers/cart_provider.dart';

class OrderScreen extends StatefulWidget {
  final String? tableId;
  final String? tableNumber;
  final String? tableStatus;

  const OrderScreen({
    super.key,
    this.tableId,
    this.tableNumber,
    this.tableStatus,
  });

  @override
  State<OrderScreen> createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> with SingleTickerProviderStateMixin {
  TabController? _tabController;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final catalog = Provider.of<CatalogProvider>(context, listen: false);
      await catalog.fetchCatalog();
      if (!mounted) return;
      if (catalog.categories.isNotEmpty) {
        setState(() {
          _tabController = TabController(
            length: catalog.categories.length,
            vsync: this,
          );
        });
      }
      
      // Initialize cart with table if applicable
      if (widget.tableId != null) {
        Provider.of<CartProvider>(context, listen: false)
            .setTable(widget.tableId, widget.tableNumber);
      }
    });
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  void _showOptionsModal(ProductModel product) {
    List<ProductOptionModel> selectedOptions = [];
    final notesController = TextEditingController();
    int quantity = 1;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        final theme = Theme.of(context);
        return StatefulBuilder(
          builder: (context, setModalState) {
            double basePrice = product.price;
            double optionsPrice = selectedOptions.fold(0.0, (sum, opt) => sum + opt.price);
            double totalItemPrice = (basePrice + optionsPrice) * quantity;

            return Padding(
              padding: EdgeInsets.only(
                top: 24,
                left: 24,
                right: 24,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    product.name,
                    style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Base price: ฿${product.price.toStringAsFixed(2)}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const Divider(height: 32),

                  // Options Checklist
                  if (product.options.isNotEmpty) ...[
                    Text(
                      'Customize (เลือกตัวเลือกเพิ่มเติม)',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    ...product.options.map((opt) {
                      final isSelected = selectedOptions.any((o) => o.id == opt.id);
                      return CheckboxListTile(
                        title: Text(opt.name),
                        secondary: Text('+ ฿${opt.price.toStringAsFixed(2)}'),
                        value: isSelected,
                        onChanged: (val) {
                          setModalState(() {
                            if (val == true) {
                              selectedOptions.add(opt);
                            } else {
                              selectedOptions.removeWhere((o) => o.id == opt.id);
                            }
                          });
                        },
                      );
                    }),
                    const SizedBox(height: 16),
                  ],

                  // Notes input
                  TextField(
                    controller: notesController,
                    decoration: InputDecoration(
                      labelText: 'Special Instructions (คำแนะนำพิเศษ)',
                      hintText: 'e.g., No sugar, extra hot',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Quantity adjusters
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Quantity (จำนวน)',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      Row(
                        children: [
                          IconButton.filledTonal(
                            icon: const Icon(Icons.remove_rounded),
                            onPressed: () {
                              if (quantity > 1) {
                                setModalState(() => quantity--);
                              }
                            },
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 16.0),
                            child: Text(
                              '$quantity',
                              style: theme.textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          IconButton.filledTonal(
                            icon: const Icon(Icons.add_rounded),
                            onPressed: () {
                              setModalState(() => quantity++);
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                  const Divider(height: 32),

                  // Add Button
                  ElevatedButton(
                    onPressed: () {
                      Provider.of<CartProvider>(context, listen: false).addToCart(
                        product,
                        quantity,
                        selectedOptions,
                        notesController.text.trim().isEmpty ? null : notesController.text.trim(),
                      );
                      Navigator.pop(context);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: theme.colorScheme.primary,
                      foregroundColor: theme.colorScheme.onPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      'Add to Order • ฿${totalItemPrice.toStringAsFixed(2)}',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final catalog = Provider.of<CatalogProvider>(context);
    final cart = Provider.of<CartProvider>(context);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.tableNumber != null ? 'Ordering: Table ${widget.tableNumber}' : 'Takeaway Order',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () {
            // Warn if cart has items
            if (cart.items.isNotEmpty) {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Discard Order?'),
                  content: const Text('You have unsaved items in your cart. Go back?'),
                  actions: [
                    TextButton(
                      child: const Text('Cancel'),
                      onPressed: () => Navigator.pop(context),
                    ),
                    TextButton(
                      child: const Text('Discard'),
                      onPressed: () {
                        cart.clearCart();
                        Navigator.pop(context); // dialog
                        context.go('/tables');
                      },
                    ),
                  ],
                ),
              );
            } else {
              context.go('/tables');
            }
          },
        ),
      ),
      body: catalog.isLoading
          ? const Center(child: CircularProgressIndicator())
          : catalog.errorMessage != null
              ? Center(
                  child: Text(
                    catalog.errorMessage!,
                    style: TextStyle(color: theme.colorScheme.error),
                  ),
                )
              : Row(
                  children: [
                    // LEFT: Catalog
                    Expanded(
                      flex: 3,
                      child: Column(
                        children: [
                          if (_tabController != null && catalog.categories.isNotEmpty) ...[
                            TabBar(
                              controller: _tabController,
                              isScrollable: true,
                              tabs: catalog.categories.map((c) => Tab(text: c.name)).toList(),
                            ),
                            Expanded(
                              child: TabBarView(
                                controller: _tabController,
                                children: catalog.categories.map((cat) {
                                  final catProducts = catalog.getProductsByCategory(cat.id);
                                  if (catProducts.isEmpty) {
                                    return Center(
                                      child: Text(
                                        'No products in this category',
                                        style: theme.textTheme.bodyMedium?.copyWith(
                                          color: theme.colorScheme.onSurfaceVariant,
                                        ),
                                      ),
                                    );
                                  }

                                  return GridView.builder(
                                    padding: const EdgeInsets.all(16),
                                    gridDelegate:
                                        const SliverGridDelegateWithMaxCrossAxisExtent(
                                      maxCrossAxisExtent: 220,
                                      crossAxisSpacing: 16,
                                      mainAxisSpacing: 16,
                                      childAspectRatio: 0.85,
                                    ),
                                    itemCount: catProducts.length,
                                    itemBuilder: (context, index) {
                                      final product = catProducts[index];
                                      return Card(
                                        elevation: 1.5,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(16),
                                        ),
                                        child: InkWell(
                                          borderRadius: BorderRadius.circular(16),
                                          onTap: () => _showOptionsModal(product),
                                          child: Padding(
                                            padding: const EdgeInsets.all(12.0),
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.stretch,
                                              children: [
                                                // Product Image Mock
                                                Expanded(
                                                  child: Container(
                                                    decoration: BoxDecoration(
                                                      color: theme.colorScheme
                                                          .primaryContainer
                                                          .withValues(alpha: 0.2),
                                                      borderRadius:
                                                          BorderRadius.circular(12),
                                                    ),
                                                    child: product.imageUrl != null
                                                        ? ClipRRect(
                                                            borderRadius:
                                                                BorderRadius.circular(12),
                                                            child: Image.network(
                                                              product.imageUrl!,
                                                              fit: BoxFit.cover,
                                                              errorBuilder:
                                                                  (context, error, stackTrace) =>
                                                                      const Icon(
                                                                Icons
                                                                    .local_cafe_rounded,
                                                                size: 36,
                                                              ),
                                                            ),
                                                          )
                                                        : const Icon(
                                                            Icons.local_cafe_rounded,
                                                            size: 36,
                                                          ),
                                                  ),
                                                ),
                                                const SizedBox(height: 8),
                                                Text(
                                                  product.name,
                                                  maxLines: 2,
                                                  overflow: TextOverflow.ellipsis,
                                                  style: theme.textTheme.titleMedium
                                                      ?.copyWith(
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                                const SizedBox(height: 4),
                                                Text(
                                                  '฿${product.price.toStringAsFixed(2)}',
                                                  style: theme.textTheme.bodyMedium
                                                      ?.copyWith(
                                                    color: theme.colorScheme.primary,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      );
                                    },
                                  );
                                }).toList(),
                              ),
                            ),
                          ] else
                            const Expanded(
                              child: Center(child: Text('No categories configured')),
                            ),
                        ],
                      ),
                    ),

                    // Vertical Divider
                    const VerticalDivider(width: 1),

                    // RIGHT: Cart Sidebar
                    Expanded(
                      flex: 2,
                      child: Container(
                        color: theme.colorScheme.surfaceContainerLow,
                        padding: const EdgeInsets.all(24.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Cart (รายการสั่งซื้อ)',
                              style: theme.textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const Divider(height: 24),

                            // Items List
                            Expanded(
                              child: cart.items.isEmpty
                                  ? Center(
                                      child: Text(
                                        'Cart is empty. Tap products to add.',
                                        style: theme.textTheme.bodyMedium?.copyWith(
                                          color: theme.colorScheme.onSurfaceVariant,
                                        ),
                                      ),
                                    )
                                  : ListView.separated(
                                      itemCount: cart.items.length,
                                      separatorBuilder: (context, index) =>
                                          const Divider(height: 16),
                                      itemBuilder: (context, index) {
                                        final item = cart.items[index];
                                        return Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Row(
                                              mainAxisAlignment:
                                                  MainAxisAlignment.spaceBetween,
                                              children: [
                                                Expanded(
                                                  child: Text(
                                                    item.product.name,
                                                    style: const TextStyle(
                                                      fontWeight: FontWeight.bold,
                                                    ),
                                                  ),
                                                ),
                                                Text(
                                                  '฿${item.totalSubtotal.toStringAsFixed(2)}',
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                              ],
                                            ),
                                            if (item.selectedOptions.isNotEmpty)
                                              Text(
                                                item.selectedOptions
                                                    .map((o) => o.name)
                                                    .join(', '),
                                                style: theme.textTheme.bodySmall
                                                    ?.copyWith(
                                                  color: theme
                                                      .colorScheme.onSurfaceVariant,
                                                ),
                                              ),
                                            if (item.notes != null)
                                              Text(
                                                'Note: "${item.notes}"',
                                                style: theme.textTheme.bodySmall
                                                    ?.copyWith(
                                                  color: Colors.red.shade800,
                                                  fontStyle: FontStyle.italic,
                                                ),
                                              ),
                                            const SizedBox(height: 8),

                                            // Quantities adjuster
                                            Row(
                                              mainAxisAlignment:
                                                  MainAxisAlignment.spaceBetween,
                                              children: [
                                                Row(
                                                  children: [
                                                    IconButton.filledTonal(
                                                      icon: const Icon(
                                                        Icons.remove_rounded,
                                                        size: 16,
                                                      ),
                                                      padding: EdgeInsets.zero,
                                                      constraints:
                                                          const BoxConstraints(),
                                                      onPressed: () => cart
                                                          .updateQuantity(
                                                              index,
                                                              item.quantity -
                                                                  1),
                                                    ),
                                                    Padding(
                                                      padding: const EdgeInsets
                                                          .symmetric(
                                                          horizontal: 12.0),
                                                      child: Text('${item.quantity}'),
                                                    ),
                                                    IconButton.filledTonal(
                                                      icon: const Icon(
                                                        Icons.add_rounded,
                                                        size: 16,
                                                      ),
                                                      padding: EdgeInsets.zero,
                                                      constraints:
                                                          const BoxConstraints(),
                                                      onPressed: () => cart
                                                          .updateQuantity(
                                                              index,
                                                              item.quantity +
                                                                  1),
                                                    ),
                                                  ],
                                                ),
                                                IconButton(
                                                  icon: const Icon(
                                                    Icons.delete_outline_rounded,
                                                    color: Colors.red,
                                                  ),
                                                  onPressed: () =>
                                                      cart.removeFromCart(index),
                                                ),
                                              ],
                                            ),
                                          ],
                                        );
                                      },
                                    ),
                            ),

                            const Divider(height: 32),

                            // Total calculations
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Subtotal (ยอดรวม)'),
                                Text('฿${cart.subtotalAmount.toStringAsFixed(2)}'),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('VAT (ภาษี 7%)'),
                                Text('฿${cart.vatAmount.toStringAsFixed(2)}'),
                              ],
                            ),
                            const Divider(height: 16),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Total (ยอดสุทธิ)',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                Text(
                                  '฿${cart.totalAmount.toStringAsFixed(2)}',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                    color: theme.colorScheme.primary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 24),

                             // Checkout Button
                            ElevatedButton(
                              onPressed: (cart.items.isEmpty || cart.isSubmitting)
                                  ? null
                                  : () async {
                                      try {
                                        final orderId = await cart.submitOrder();
                                        if (context.mounted) {
                                          cart.clearCart();
                                          context.push('/checkout?orderId=$orderId');
                                        }
                                      } catch (e) {
                                        if (context.mounted) {
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(
                                              content: Text('Failed to submit order: $e'),
                                              backgroundColor: theme.colorScheme.error,
                                            ),
                                          );
                                        }
                                      }
                                    },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: theme.colorScheme.primary,
                                foregroundColor: theme.colorScheme.onPrimary,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: cart.isSubmitting
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Text(
                                      'Checkout (คิดเงิน)',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
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
