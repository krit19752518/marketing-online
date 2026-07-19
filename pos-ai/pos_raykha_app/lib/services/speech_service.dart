import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';

class SpeechService {
  final SpeechToText _speechToText = SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();
  
  bool _isSpeechInitialized = false;
  bool get isListening => _speechToText.isListening;

  Future<void> init() async {
    try {
      _isSpeechInitialized = await _speechToText.initialize(
        onError: (val) => debugPrint('STT Error: $val'),
        onStatus: (val) => debugPrint('STT Status: $val'),
      );
      
      // Configure Text to Speech settings
      await _flutterTts.setLanguage("th-TH");
      await _flutterTts.setSpeechRate(0.55); // Comfortable reading speed
      await _flutterTts.setVolume(1.0);
      await _flutterTts.setPitch(1.0);
    } catch (e) {
      debugPrint("Failed to initialize speech services: $e");
    }
  }

  Future<void> startListening(Function(String) onWordsRecognized) async {
    if (!_isSpeechInitialized) {
      await init();
    }
    
    if (_isSpeechInitialized && !_speechToText.isListening) {
      await _speechToText.listen(
        listenOptions: SpeechListenOptions(localeId: 'th_TH'),
        onResult: (result) {
          if (result.recognizedWords.isNotEmpty) {
            onWordsRecognized(result.recognizedWords);
          }
        },
      );
    }
  }

  Future<void> stopListening() async {
    if (_speechToText.isListening) {
      await _speechToText.stop();
    }
  }

  Future<void> speak(String text) async {
    // Stop any active speech before speaking again
    await stopSpeaking();
    if (text.isNotEmpty) {
      // Remove SQL blocks from readout so TTS doesn't read queries out loud
      String speakText = text.replaceAll(RegExp(r'```sql[\s\S]*?```'), '');
      speakText = speakText.replaceAll(RegExp(r'```json[\s\S]*?```'), '');
      await _flutterTts.speak(speakText);
    }
  }

  Future<void> stopSpeaking() async {
    await _flutterTts.stop();
  }
}
