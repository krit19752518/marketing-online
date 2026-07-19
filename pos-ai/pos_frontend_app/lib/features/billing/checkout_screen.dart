import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../services/api_service.dart';

class CheckoutScreen extends StatefulWidget {
  final String orderId;

  const CheckoutScreen({super.key, required this.orderId});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  Map<String, dynamic>? _orderData;
  bool _isLoading = true;
  String? _errorMessage;

  String _paymentMethod = 'CASH'; // 'CASH', 'QR_MOCK', 'CREDIT_CARD'
  final _cashController = TextEditingController();
  final double _discount = 0.0;
  double _change = 0.0;
  bool _isCheckingOut = false;

  @override
  void initState() {
    super.initState();
    _fetchOrderDetails();
    _cashController.addListener(_calculateChange);
  }

  @override
  void dispose() {
    _cashController.dispose();
    super.dispose();
  }

  Future<void> _fetchOrderDetails() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await ApiService.get('/orders/${widget.orderId}');
      setState(() {
        _orderData = jsonDecode(response.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load bill details: $e';
        _isLoading = false;
      });
    }
  }

  double get _totalAmount {
    if (_orderData == null) return 0.0;
    return (_orderData!['totalAmount'] as num).toDouble();
  }

  double get _finalAmountDue {
    return _totalAmount - _discount;
  }

  void _calculateChange() {
    final paid = double.tryParse(_cashController.text) ?? 0.0;
    final changeVal = paid - _finalAmountDue;
    setState(() {
      _change = changeVal > 0 ? changeVal : 0.0;
    });
  }

  void _applyQuickCash(double amount) {
    _cashController.text = amount.toStringAsFixed(0);
    _calculateChange();
  }

  Future<void> _processCheckout() async {
    final paid = _paymentMethod == 'CASH'
        ? (double.tryParse(_cashController.text) ?? 0.0)
        : _finalAmountDue;

    if (paid < _finalAmountDue) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Paid amount cannot be less than the total due amount'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isCheckingOut = true;
    });

    try {
      await ApiService.post('/orders/${widget.orderId}/checkout', {
        'paymentMethod': _paymentMethod,
        'amountPaid': paid,
        'discount': _discount,
      });

      if (mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            icon: const Icon(
              Icons.check_circle_outline_rounded,
              color: Colors.green,
              size: 48,
            ),
            title: const Text('Payment Successful'),
            content: Text(
              _paymentMethod == 'CASH'
                  ? 'Payment processed.\nChange: ฿${_change.toStringAsFixed(2)}'
                  : 'Payment processed successfully.',
              textAlign: TextAlign.center,
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context); // dialog
                  context.go('/tables');
                },
                child: const Text('Back to Tables'),
              ),
            ],
          ),
        );
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Checkout failed: ${e.message}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() {
        _isCheckingOut = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (_errorMessage != null || _orderData == null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                _errorMessage ?? 'Something went wrong',
                style: TextStyle(color: theme.colorScheme.error),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchOrderDetails,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final items = _orderData!['items'] as List;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Billing & Checkout', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Row(
        children: [
          // LEFT: Order Summary List
          Expanded(
            flex: 3,
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Order Summary (สรุปรายการอาหาร)',
                    style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: ListView.separated(
                      itemCount: items.length,
                      separatorBuilder: (context, index) => const Divider(),
                      itemBuilder: (context, index) {
                        final item = items[index];
                        final opts = item['selectedOpts'] as List? ?? [];
                        final notes = item['notes'] as String?;

                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    '${item['product']['name']} x${item['quantity']}',
                                    style: const TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  Text('฿${(item['subtotal'] as num).toDouble().toStringAsFixed(2)}'),
                                ],
                              ),
                              if (opts.isNotEmpty)
                                Text(
                                  opts.map((o) => o['name']).join(', '),
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              if (notes != null)
                                Text(
                                  'Note: "$notes"',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: Colors.red.shade800,
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                  const Divider(height: 32),
                  _buildSummaryRow('Subtotal', _totalAmount / 1.07), // 7% VAT exclusive base
                  const SizedBox(height: 8),
                  _buildSummaryRow('VAT (7%)', _totalAmount - (_totalAmount / 1.07)),
                  const Divider(height: 24),
                  _buildSummaryRow(
                    'Total Amount',
                    _totalAmount,
                    isBold: true,
                    fontSize: 20,
                    color: theme.colorScheme.primary,
                  ),
                ],
              ),
            ),
          ),

          const VerticalDivider(width: 1),

          // RIGHT: Payment Processor
          Expanded(
            flex: 2,
            child: Container(
              color: theme.colorScheme.surfaceContainerLow,
              padding: const EdgeInsets.all(24.0),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Select Payment Method',
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        _buildPaymentMethodButton('CASH', Icons.money_rounded, 'Cash'),
                        const SizedBox(width: 12),
                        _buildPaymentMethodButton('QR_MOCK', Icons.qr_code_2_rounded, 'QR Code'),
                      ],
                    ),
                    const Divider(height: 32),

                    // Cash Payment Mode View
                    if (_paymentMethod == 'CASH') ...[
                      Text(
                        'Cash Payment details',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      // Quick Cash Buttons
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _quickCashButton(50.0),
                          _quickCashButton(100.0),
                          _quickCashButton(500.0),
                          _quickCashButton(1000.0),
                          _quickCashButton(_finalAmountDue), // Exact change button
                        ],
                      ),
                      const SizedBox(height: 24),
                      TextField(
                        controller: _cashController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText: 'Cash Received (รับเงินสด)',
                          prefixText: '฿',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.secondaryContainer.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Change (เงินทอน)',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              '฿${_change.toStringAsFixed(2)}',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: theme.colorScheme.secondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ]

                    // QR Payment Mode View
                    else if (_paymentMethod == 'QR_MOCK') ...[
                      Text(
                        'Scan QR Code to Pay',
                        textAlign: TextAlign.center,
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 24),
                      Center(
                        child: Container(
                          width: 200,
                          height: 200,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: Colors.grey.shade300, width: 2),
                          ),
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              // Mock QR Graphic
                              Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.qr_code_scanner_rounded, size: 80, color: theme.colorScheme.primary),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Thai QR Payment',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                      color: theme.colorScheme.primary,
                                    ),
                                  ),
                                ],
                              ),
                              Positioned(
                                top: 8,
                                right: 8,
                                child: Icon(Icons.check_circle_outline, color: theme.colorScheme.primary, size: 20),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Total Due: ฿${_finalAmountDue.toStringAsFixed(2)}',
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],

                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: _isCheckingOut ? null : _processCheckout,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: theme.colorScheme.primary,
                        foregroundColor: theme.colorScheme.onPrimary,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: _isCheckingOut
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text(
                              'Confirm Payment (ยืนยันชำระเงิน)',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(
    String label,
    double value, {
    bool isBold = false,
    double fontSize = 14,
    Color? color,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            fontSize: fontSize,
          ),
        ),
        Text(
          '฿${value.toStringAsFixed(2)}',
          style: TextStyle(
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            fontSize: fontSize,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildPaymentMethodButton(String method, IconData icon, String label) {
    final isSelected = _paymentMethod == method;
    final theme = Theme.of(context);

    return Expanded(
      child: OutlinedButton(
        onPressed: () {
          setState(() {
            _paymentMethod = method;
            _calculateChange();
          });
        },
        style: OutlinedButton.styleFrom(
          backgroundColor: isSelected ? theme.colorScheme.primary : Colors.transparent,
          foregroundColor: isSelected ? theme.colorScheme.onPrimary : theme.colorScheme.primary,
          side: BorderSide(color: theme.colorScheme.primary),
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: Column(
          children: [
            Icon(icon),
            const SizedBox(height: 6),
            Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _quickCashButton(double amount) {
    return ActionChip(
      label: Text('฿${amount.toStringAsFixed(0)}'),
      onPressed: () => _applyQuickCash(amount),
    );
  }
}
