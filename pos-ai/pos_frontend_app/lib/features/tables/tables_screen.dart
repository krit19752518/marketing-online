import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/table_provider.dart';

class TablesScreen extends StatefulWidget {
  const TablesScreen({super.key});

  @override
  State<TablesScreen> createState() => _TablesScreenState();
}

class _TablesScreenState extends State<TablesScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<TableProvider>(context, listen: false).fetchTables();
    });
  }

  Color _getStatusColor(String status, ThemeData theme) {
    switch (status) {
      case 'VACANT':
        return Colors.teal;
      case 'OCCUPIED':
        return Colors.orange.shade800;
      case 'BILLING':
        return Colors.amber.shade700;
      default:
        return theme.colorScheme.outline;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'VACANT':
        return Icons.check_circle_outline_rounded;
      case 'OCCUPIED':
        return Icons.people_outline_rounded;
      case 'BILLING':
        return Icons.receipt_long_rounded;
      default:
        return Icons.help_outline_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final tableProv = Provider.of<TableProvider>(context);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'POS-AI Table Layout',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            if (auth.name != null)
              Text(
                '${auth.name} (${auth.role})',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Kitchen Queue',
            icon: const Icon(Icons.restaurant_menu_rounded),
            onPressed: () => context.push('/kitchen'),
          ),
          IconButton(
            tooltip: 'Refresh Tables',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => tableProv.fetchTables(),
          ),
          IconButton(
            tooltip: 'Logout',
            icon: const Icon(Icons.logout_rounded),
            onPressed: () async {
              await auth.logout();
              if (context.mounted) {
                context.go('/login');
              }
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: tableProv.isLoading
          ? const Center(child: CircularProgressIndicator())
          : tableProv.errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline_rounded,
                        color: theme.colorScheme.error,
                        size: 48,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        tableProv.errorMessage!,
                        style: TextStyle(color: theme.colorScheme.error),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => tableProv.fetchTables(),
                        child: const Text('Try Again'),
                      ),
                    ],
                  ),
                )
              : Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Legend / Status indicator row
                      Card(
                        elevation: 0,
                        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            vertical: 12,
                            horizontal: 16,
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceAround,
                            children: [
                              _buildLegendItem('Vacant (ว่าง)', Colors.teal),
                              _buildLegendItem('Occupied (มีลูกค้า)', Colors.orange.shade800),
                              _buildLegendItem('Billing (เรียกเช็กบิล)', Colors.amber.shade700),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Tables Grid
                      Expanded(
                        child: tableProv.tables.isEmpty
                            ? Center(
                                child: Text(
                                  'No tables configured. Please add tables in Manager App.',
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              )
                            : GridView.builder(
                                gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                                  maxCrossAxisExtent: 180,
                                  crossAxisSpacing: 16,
                                  mainAxisSpacing: 16,
                                  childAspectRatio: 1.1,
                                ),
                                itemCount: tableProv.tables.length,
                                itemBuilder: (context, index) {
                                  final table = tableProv.tables[index];
                                  final color = _getStatusColor(table.status, theme);
                                  final icon = _getStatusIcon(table.status);

                                  return Card(
                                    elevation: 2,
                                    shadowColor: Colors.black12,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(20),
                                      side: BorderSide(
                                        color: color.withValues(alpha: 0.5),
                                        width: 1.5,
                                      ),
                                    ),
                                    child: InkWell(
                                      borderRadius: BorderRadius.circular(20),
                                      onTap: () {
                                        // Tap navigates to order screen passing the selected table info
                                        context.push('/order?tableId=${table.id}&tableNumber=${table.number}&tableStatus=${table.status}');
                                      },
                                      child: Padding(
                                        padding: const EdgeInsets.all(16.0),
                                        child: Column(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            Icon(
                                              icon,
                                              color: color,
                                              size: 32,
                                            ),
                                            const SizedBox(height: 8),
                                            Text(
                                              'Table ${table.number}',
                                              style: theme.textTheme.titleMedium?.copyWith(
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Container(
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: 8,
                                                vertical: 2,
                                              ),
                                              decoration: BoxDecoration(
                                                color: color.withValues(alpha: 0.1),
                                                borderRadius: BorderRadius.circular(8),
                                              ),
                                              child: Text(
                                                table.status,
                                                style: theme.textTheme.bodySmall?.copyWith(
                                                  color: color,
                                                  fontWeight: FontWeight.w600,
                                                  fontSize: 10,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  );
                                },
                              ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}
