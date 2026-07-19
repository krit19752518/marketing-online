import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../providers/auth_provider.dart';
import '../../providers/chat_provider.dart';
import '../../services/speech_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with SingleTickerProviderStateMixin {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final SpeechService _speechService = SpeechService();
  
  bool _isTtsEnabled = true;
  bool _isRecording = false;
  AnimationController? _micPulseController;

  @override
  void initState() {
    super.initState();
    _speechService.init();
    _micPulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat(reverse: true);
    
    // Fetch initial sessions list
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProv = context.read<ChatProvider>();
      chatProv.fetchSessions().then((_) {
        // If there are no sessions, auto-create one
        if (chatProv.sessions.isEmpty) {
          chatProv.createNewSession();
        } else {
          // Select the latest session
          chatProv.selectSession(chatProv.sessions.first);
        }
      });
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _micPulseController?.dispose();
    _speechService.stopSpeaking();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 100,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _handleSendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _messageController.clear();
    _scrollToBottom();

    final chatProv = context.read<ChatProvider>();
    final aiResponse = await chatProv.sendMessage(text);
    
    _scrollToBottom();
    
    // Trigger TTS voice readout if enabled
    if (_isTtsEnabled && aiResponse != null) {
      _speechService.speak(aiResponse);
    }
  }

  void _toggleRecording() async {
    if (_isRecording) {
      setState(() => _isRecording = false);
      await _speechService.stopListening();
      _handleSendMessage();
    } else {
      setState(() => _isRecording = true);
      await _speechService.startListening((words) {
        setState(() {
          _messageController.text = words;
        });
      });
    }
  }

  Widget _buildChatSessionsSidebar(BuildContext context) {
    final theme = Theme.of(context);
    final chatProv = context.watch<ChatProvider>();
    final auth = context.watch<AuthProvider>();

    return Drawer(
      child: Container(
        color: theme.colorScheme.surfaceContainerLow,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            UserAccountsDrawerHeader(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [theme.colorScheme.primary, theme.colorScheme.tertiary],
                ),
              ),
              currentAccountPicture: CircleAvatar(
                backgroundColor: theme.colorScheme.onPrimary,
                child: Text(
                  auth.name?.substring(0, 1).toUpperCase() ?? 'U',
                  style: TextStyle(fontWeight: FontWeight.bold, color: theme.colorScheme.primary, fontSize: 24),
                ),
              ),
              accountName: Text(auth.name ?? 'Manager', style: const TextStyle(fontWeight: FontWeight.bold)),
              accountEmail: Text('Store: ${auth.tenantName ?? 'POS Restaurant'}'),
            ),

            // New Conversation Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: ElevatedButton.icon(
                icon: const Icon(Icons.add_comment_rounded),
                label: const Text('New Conversation'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: theme.colorScheme.primaryContainer,
                  foregroundColor: theme.colorScheme.onPrimaryContainer,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: () {
                  chatProv.createNewSession();
                  Navigator.pop(context);
                },
              ),
            ),
            const Divider(),

            // Sessions List
            Expanded(
              child: chatProv.isSessionsLoading
                  ? const Center(child: CircularProgressIndicator())
                  : chatProv.sessions.isEmpty
                      ? Center(
                          child: Text(
                            'No sessions found.',
                            style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                          ),
                        )
                      : ListView.builder(
                          itemCount: chatProv.sessions.length,
                          itemBuilder: (context, index) {
                            final sess = chatProv.sessions[index];
                            final isActive = chatProv.activeSession != null && chatProv.activeSession!['id'] == sess['id'];

                            return ListTile(
                              selected: isActive,
                              selectedTileColor: theme.colorScheme.primaryContainer.withValues(alpha: 0.2),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                              leading: Icon(
                                Icons.chat_bubble_outline_rounded,
                                color: isActive ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant,
                              ),
                              title: Text(
                                sess['title'] ?? 'New Conversation',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                                  color: isActive ? theme.colorScheme.primary : theme.colorScheme.onSurface,
                                ),
                              ),
                              subtitle: Text(
                                sess['snippet'] ?? '',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: theme.colorScheme.onSurfaceVariant,
                                ),
                              ),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline_rounded, size: 20),
                                onPressed: () {
                                  showDialog(
                                    context: context,
                                    builder: (context) => AlertDialog(
                                      title: const Text('Delete Session?'),
                                      content: const Text('Are you sure you want to delete this chat history?'),
                                      actions: [
                                        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                                        TextButton(
                                          onPressed: () {
                                            chatProv.deleteSession(sess['id']);
                                            Navigator.pop(context);
                                          },
                                          child: const Text('Delete', style: TextStyle(color: Colors.red)),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                              ),
                              onTap: () {
                                chatProv.selectSession(sess);
                                Navigator.pop(context);
                              },
                            );
                          },
                        ),
            ),
            const Divider(),
            
            // Logout
            ListTile(
              leading: Icon(Icons.logout_rounded, color: theme.colorScheme.error),
              title: Text('Logout', style: TextStyle(color: theme.colorScheme.error)),
              onTap: () async {
                await auth.logout();
                if (context.mounted) context.go('/login');
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildSQLWidget(String sql, String? jsonResult, ThemeData theme) {
    List<dynamic> rows = [];
    if (jsonResult != null && jsonResult.isNotEmpty) {
      try {
        final decoded = jsonDecode(jsonResult);
        if (decoded is List) {
          rows = decoded;
        }
      } catch (_) {}
    }

    return Card(
      elevation: 0,
      color: theme.colorScheme.surfaceContainerHigh.withValues(alpha: 0.6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: ExpansionTile(
        leading: Icon(Icons.terminal_rounded, color: theme.colorScheme.secondary),
        title: Text(
          'Query Executor Logs',
          style: theme.textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.secondary,
          ),
        ),
        subtitle: const Text('Tap to view generated SQL and database output', style: TextStyle(fontSize: 11)),
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // SQL Section
                const Text('GENERATED SQL:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.grey)),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black87,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    sql,
                    style: const TextStyle(color: Colors.lightGreenAccent, fontFamily: 'monospace', fontSize: 12),
                  ),
                ),
                const SizedBox(height: 16),

                // DB Results Table
                const Text('QUERY RESULTS:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.grey)),
                const SizedBox(height: 6),
                rows.isEmpty
                    ? const Text('No rows returned or empty result.')
                    : SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: DataTable(
                          columns: (rows.first as Map<String, dynamic>)
                              .keys
                              .map((k) => DataColumn(label: Text(k, style: const TextStyle(fontWeight: FontWeight.bold))))
                              .toList(),
                          rows: rows.map((r) {
                            return DataRow(
                              cells: (r as Map<String, dynamic>)
                                  .values
                                  .map((v) => DataCell(Text(v.toString())))
                                  .toList(),
                            );
                          }).toList(),
                        ),
                      ),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildMessageItem(dynamic msg, ThemeData theme) {
    final isUser = msg['role'] == 'user';
    final hasSQL = msg['query_sql'] != null && msg['query_sql'].toString().isNotEmpty;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(Icons.assistant_rounded, color: theme.colorScheme.primary, size: 20),
            ),
            const SizedBox(width: 12),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isUser
                        ? theme.colorScheme.primary
                        : theme.colorScheme.surfaceContainerHigh,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(20),
                      topRight: const Radius.circular(20),
                      bottomLeft: isUser ? const Radius.circular(20) : Radius.zero,
                      bottomRight: isUser ? Radius.zero : const Radius.circular(20),
                    ),
                  ),
                  child: Text(
                    msg['content'],
                    style: TextStyle(
                      color: isUser ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface,
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                ),
                
                // Show Query SQL and Result if present
                if (hasSQL)
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 600),
                    child: _buildSQLWidget(msg['query_sql'], msg['query_result'], theme),
                  ),

                // TTS speak icon for AI responses
                if (!isUser) ...[
                  const SizedBox(height: 4),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.volume_up_rounded, size: 18),
                        onPressed: () => _speechService.speak(msg['content']),
                      ),
                      Text('Speak', style: theme.textTheme.bodySmall),
                    ],
                  ),
                ],
              ],
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 12),
            CircleAvatar(
              backgroundColor: theme.colorScheme.secondaryContainer,
              child: const Icon(Icons.person_rounded, size: 20),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chatProv = context.watch<ChatProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              chatProv.activeSession?['title'] ?? 'RayKha Chat',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            Text(
              'Store database agent connected',
              style: TextStyle(fontSize: 11, color: theme.colorScheme.primary),
            ),
          ],
        ),
        actions: [
          // TTS Readout toggler
          IconButton(
            icon: Icon(
              _isTtsEnabled ? Icons.record_voice_over_rounded : Icons.voice_over_off_rounded,
              color: _isTtsEnabled ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant,
            ),
            tooltip: _isTtsEnabled ? 'Mute AI Auto Voice' : 'Enable AI Auto Voice',
            onPressed: () {
              setState(() => _isTtsEnabled = !_isTtsEnabled);
              if (!_isTtsEnabled) {
                _speechService.stopSpeaking();
              }
            },
          ),
          const SizedBox(width: 12),
        ],
      ),
      drawer: _buildChatSessionsSidebar(context),
      body: SafeArea(
        child: Column(
          children: [
            // Chat Messages List
            Expanded(
              child: chatProv.isMessagesLoading
                  ? const Center(child: CircularProgressIndicator())
                  : chatProv.messages.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.chat_bubble_outline_rounded, size: 64, color: theme.colorScheme.outlineVariant),
                              const SizedBox(height: 16),
                              Text(
                                'Speak or type a message to start conversation.',
                                style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'e.g. "ยอดขายเมื่อวานนี้เท่าไหร่", "มีของอะไรหมดบ้าง"',
                                style: TextStyle(color: theme.colorScheme.primary, fontSize: 12),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          controller: _scrollController,
                          itemCount: chatProv.messages.length,
                          itemBuilder: (context, index) {
                            return _buildMessageItem(chatProv.messages[index], theme);
                          },
                        ),
            ),

            // Loading while AI is processing
            if (chatProv.isSending)
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                    Text('Raykha is thinking & querying database...', style: theme.textTheme.bodySmall),
                  ],
                ),
              ),

            // Chat Input Panel
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
              child: Row(
                children: [
                  // Microphone STT Button with pulsing animation
                  Stack(
                    alignment: Alignment.center,
                    children: [
                      if (_isRecording)
                        AnimatedBuilder(
                          animation: _micPulseController!,
                          builder: (context, child) {
                            return Container(
                              height: 56 * _micPulseController!.value + 20,
                              width: 56 * _micPulseController!.value + 20,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.red.withValues(alpha: 0.15),
                              ),
                            );
                          },
                        ),
                      FloatingActionButton(
                        onPressed: _toggleRecording,
                        heroTag: 'mic-fab',
                        backgroundColor: _isRecording ? Colors.red : theme.colorScheme.secondaryContainer,
                        foregroundColor: _isRecording ? Colors.white : theme.colorScheme.onSecondaryContainer,
                        elevation: 0,
                        shape: const CircleBorder(),
                        child: Icon(_isRecording ? Icons.mic_rounded : Icons.mic_none_rounded),
                      ),
                    ],
                  ),
                  const SizedBox(width: 12),

                  // Text input field
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHigh,
                        borderRadius: BorderRadius.circular(32),
                        border: Border.all(color: theme.colorScheme.outlineVariant),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _messageController,
                              decoration: const InputDecoration(
                                hintText: 'Ask RayKha...',
                                border: InputBorder.none,
                              ),
                              onSubmitted: (_) => _handleSendMessage(),
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.send_rounded, color: theme.colorScheme.primary),
                            onPressed: _handleSendMessage,
                          ),
                        ],
                      ),
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
}
