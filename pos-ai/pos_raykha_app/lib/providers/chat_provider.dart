import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ChatProvider extends ChangeNotifier {
  List<dynamic> _sessions = [];
  List<dynamic> _messages = [];
  Map<String, dynamic>? _activeSession;

  bool _isSessionsLoading = false;
  bool _isMessagesLoading = false;
  bool _isSending = false;

  List<dynamic> get sessions => _sessions;
  List<dynamic> get messages => _messages;
  Map<String, dynamic>? get activeSession => _activeSession;

  bool get isSessionsLoading => _isSessionsLoading;
  bool get isMessagesLoading => _isMessagesLoading;
  bool get isSending => _isSending;

  // Fetch all chat sessions (sidebar list with snippets)
  Future<void> fetchSessions() async {
    _isSessionsLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.get('/sessions');
      if (response.statusCode == 200) {
        _sessions = jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Error fetching sessions: $e");
    } finally {
      _isSessionsLoading = false;
      notifyListeners();
    }
  }

  // Create a new session and auto-select it
  Future<void> createNewSession({String? title}) async {
    _isMessagesLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.post('/sessions', {
        'title': title ?? 'New Conversation',
      });
      if (response.statusCode == 200) {
        final newSess = jsonDecode(response.body);
        _activeSession = newSess;
        _messages = [];
        await fetchSessions();
      }
    } catch (e) {
      debugPrint("Error creating session: $e");
    } finally {
      _isMessagesLoading = false;
      notifyListeners();
    }
  }

  // Select an existing session and fetch its messages
  Future<void> selectSession(Map<String, dynamic> session) async {
    _activeSession = session;
    _messages = [];
    _isMessagesLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.get('/sessions/${session['id']}/messages');
      if (response.statusCode == 200) {
        _messages = jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Error fetching messages: $e");
    } finally {
      _isMessagesLoading = false;
      notifyListeners();
    }
  }

  // Send a message to the active session
  Future<String?> sendMessage(String content) async {
    if (_activeSession == null) return null;
    
    _isSending = true;
    // Add user message to UI immediately for fast rendering
    final tempUserMsg = {
      'id': 'temp-user',
      'role': 'user',
      'content': content,
      'created_at': DateTime.now().toIso8601String()
    };
    _messages.add(tempUserMsg);
    notifyListeners();

    try {
      final response = await ApiService.post('/chat', {
        'session_id': _activeSession!['id'],
        'content': content,
      });

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Remove temporary message and fetch official messages to align IDs/SQL fields
        final messagesResponse = await ApiService.get('/sessions/${_activeSession!['id']}/messages');
        if (messagesResponse.statusCode == 200) {
          _messages = jsonDecode(messagesResponse.body);
        }
        
        // Refresh sidebar snippets list
        await fetchSessions();
        
        // Return the AI response string for Text-to-Speech triggers
        return data['ai_response'];
      }
    } catch (e) {
      debugPrint("Error sending message: $e");
    } finally {
      _isSending = false;
      notifyListeners();
    }
    return null;
  }

  // Delete session
  Future<void> deleteSession(String sessionId) async {
    try {
      final response = await ApiService.delete('/sessions/$sessionId');
      if (response.statusCode == 200) {
        if (_activeSession != null && _activeSession!['id'] == sessionId) {
          _activeSession = null;
          _messages = [];
        }
        await fetchSessions();
      }
    } catch (e) {
      debugPrint("Error deleting session: $e");
    }
  }
}
