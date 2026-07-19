import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _analyticsData;
  bool _isLoading = true;
  String? _errorMessage;
  String _filterRange = '7days'; // 'today', '7days', '30days'

  @override
  void initState() {
    super.initState();
    _fetchAnalytics();
  }

  Future<void> _fetchAnalytics() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final now = DateTime.now();
    DateTime startDate;

    if (_filterRange == 'today') {
      startDate = DateTime(now.year, now.month, now.day);
    } else if (_filterRange == '30days') {
      startDate = now.subtract(const Duration(days: 30));
    } else {
      // default 7 days
      startDate = now.subtract(const Duration(days: 7));
    }

    final startDateStr = startDate.toIso8601String().split('T')[0];
    final endDateStr = now.toIso8601String().split('T')[0];

    try {
      final response = await ApiService.get(
        '/analytics/dashboard?startDate=$startDateStr&endDate=$endDateStr',
      );
      setState(() {
        _analyticsData = jsonDecode(response.body);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load dashboard data: $e';
        _isLoading = false;
      });
    }
  }

  Widget _buildSummaryCard(
    String title,
    String value,
    IconData icon,
    Color color,
    ThemeData theme,
  ) {
    return Card(
      elevation: 2,
      shadowColor: Colors.black12,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Row(
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: color.withValues(alpha: 0.1),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSidebar(BuildContext context, String currentRoute) {
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
          _sidebarItem(context, Icons.dashboard_rounded, 'Dashboard', '/dashboard', currentRoute == '/dashboard'),
          _sidebarItem(context, Icons.restaurant_menu_rounded, 'Menu Items', '/menu', currentRoute == '/menu'),
          _sidebarItem(context, Icons.table_restaurant_rounded, 'Tables', '/tables', currentRoute == '/tables'),
          _sidebarItem(context, Icons.inventory_2_rounded, 'Inventory', '/inventory', currentRoute == '/inventory'),
          _sidebarItem(context, Icons.badge_rounded, 'Employees', '/employees', currentRoute == '/employees'),
          const Spacer(),
          const Divider(),
          _sidebarItem(context, Icons.logout_rounded, 'Logout', '/login', false, isLogout: true),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _sidebarItem(
    BuildContext context,
    IconData icon,
    String label,
    String route,
    bool isSelected, {
    bool isLogout = false,
  }) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 4.0),
      child: Material(
        color: Colors.transparent,
        child: ListTile(
          leading: Icon(
            icon,
            color: isSelected ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant,
          ),
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

    if (_isLoading) {
      return Scaffold(
        body: Row(
          children: [
            _buildSidebar(context, '/dashboard'),
            const VerticalDivider(width: 1),
            const Expanded(child: Center(child: CircularProgressIndicator())),
          ],
        ),
      );
    }

    if (_errorMessage != null || _analyticsData == null) {
      return Scaffold(
        body: Row(
          children: [
            _buildSidebar(context, '/dashboard'),
            const VerticalDivider(width: 1),
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _errorMessage ?? 'Something went wrong',
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _fetchAnalytics,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Extract analytic fields
    final totalRevenue = (_analyticsData!['totalRevenue'] as num).toDouble();
    final totalOrders = _analyticsData!['totalOrders'] as int;
    final averageOrderValue = (_analyticsData!['averageOrderValue'] as num).toDouble();
    final topProducts = _analyticsData!['topProducts'] as List? ?? [];
    final salesByCategory = _analyticsData!['salesByCategory'] as List? ?? [];
    final dailySales = _analyticsData!['dailySales'] as List? ?? [];

    return Scaffold(
      body: Row(
        children: [
          // Sidebar Menu
          _buildSidebar(context, '/dashboard'),
          const VerticalDivider(width: 1),

          // Main Dashboard Page
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Page Header and Filter
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Dashboard Overview',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      DropdownButton<String>(
                        value: _filterRange,
                        onChanged: (val) {
                          if (val != null) {
                            setState(() {
                              _filterRange = val;
                            });
                            _fetchAnalytics();
                          }
                        },
                        items: const [
                          DropdownMenuItem(value: 'today', child: Text('Today')),
                          DropdownMenuItem(value: '7days', child: Text('Last 7 Days')),
                          DropdownMenuItem(value: '30days', child: Text('Last 30 Days')),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 28),

                  // Summary Cards Row
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final cardWidth = (constraints.maxWidth - 32) / 3;
                      return Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          SizedBox(
                            width: cardWidth,
                            child: _buildSummaryCard(
                              'Total Revenue',
                              '฿${totalRevenue.toStringAsFixed(2)}',
                              Icons.payments_rounded,
                              Colors.teal,
                              theme,
                            ),
                          ),
                          SizedBox(
                            width: cardWidth,
                            child: _buildSummaryCard(
                              'Total Orders',
                              '$totalOrders',
                              Icons.shopping_bag_rounded,
                              Colors.blue.shade700,
                              theme,
                            ),
                          ),
                          SizedBox(
                            width: cardWidth,
                            child: _buildSummaryCard(
                              'Average Order Value',
                              '฿${averageOrderValue.toStringAsFixed(2)}',
                              Icons.insights_rounded,
                              Colors.purple.shade700,
                              theme,
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 32),

                  // Line Chart for Daily Revenue
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Revenue Trend (฿)',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 24),
                          SizedBox(
                            height: 250,
                            child: dailySales.isEmpty
                                ? const Center(child: Text('No trend data available'))
                                : LineChart(
                                    LineChartData(
                                      gridData: const FlGridData(show: false),
                                      titlesData: FlTitlesData(
                                        rightTitles: const AxisTitles(
                                          sideTitles: SideTitles(showTitles: false),
                                        ),
                                        topTitles: const AxisTitles(
                                          sideTitles: SideTitles(showTitles: false),
                                        ),
                                        bottomTitles: AxisTitles(
                                          sideTitles: SideTitles(
                                            showTitles: true,
                                            getTitlesWidget: (val, meta) {
                                              final idx = val.toInt();
                                              if (idx >= 0 && idx < dailySales.length) {
                                                final date = dailySales[idx]['date'] as String;
                                                return Padding(
                                                  padding: const EdgeInsets.only(top: 8.0),
                                                  child: Text(
                                                    date.substring(5), // MM-DD
                                                    style: const TextStyle(fontSize: 10),
                                                  ),
                                                );
                                              }
                                              return const SizedBox();
                                            },
                                            interval: 1,
                                          ),
                                        ),
                                      ),
                                      borderData: FlBorderData(show: false),
                                      lineBarsData: [
                                        LineChartBarData(
                                          spots: List.generate(dailySales.length, (idx) {
                                            final rev = (dailySales[idx]['revenue'] as num).toDouble();
                                            return FlSpot(idx.toDouble(), rev);
                                          }),
                                          isCurved: true,
                                          color: theme.colorScheme.primary,
                                          barWidth: 4,
                                          belowBarData: BarAreaData(
                                            show: true,
                                            color: theme.colorScheme.primary.withValues(alpha: 0.15),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Bottom Grid: Sales by Category & Top Products
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Category Sales List
                      Expanded(
                        child: Card(
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          child: Padding(
                            padding: const EdgeInsets.all(24.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Sales by Category',
                                  style: theme.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const Divider(height: 32),
                                if (salesByCategory.isEmpty)
                                  const Center(child: Text('No category data available'))
                                else
                                  ...salesByCategory.map((cat) {
                                    final revenue = (cat['revenue'] as num).toDouble();
                                    return Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            cat['name'] as String,
                                            style: const TextStyle(fontWeight: FontWeight.w500),
                                          ),
                                          Text(
                                            '฿${revenue.toStringAsFixed(2)}',
                                            style: const TextStyle(fontWeight: FontWeight.bold),
                                          ),
                                        ],
                                      ),
                                    );
                                  }),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 24),

                      // Top Products List
                      Expanded(
                        child: Card(
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          child: Padding(
                            padding: const EdgeInsets.all(24.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Top Selling Products',
                                  style: theme.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const Divider(height: 32),
                                if (topProducts.isEmpty)
                                  const Center(child: Text('No product data available'))
                                else
                                  ...topProducts.map((prod) {
                                    final quantity = prod['quantity'] as int;
                                    final rev = (prod['revenue'] as num).toDouble();
                                    return Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              prod['name'] as String,
                                              style: const TextStyle(fontWeight: FontWeight.w500),
                                            ),
                                          ),
                                          Text(
                                            '$quantity sold (฿${rev.toStringAsFixed(2)})',
                                            style: const TextStyle(fontWeight: FontWeight.bold),
                                          ),
                                        ],
                                      ),
                                    );
                                  }),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
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
