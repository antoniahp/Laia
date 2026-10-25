import 'package:flutter_tts/flutter_tts.dart';

import '../i18n.dart';

/// La voz de Laia dentro del móvil (el lector de voz de Android), para el modo manos libres.
class Speaker {
  static final _tts = FlutterTts();
  static String? _ready;

  /// Dice la frase y espera a que termine. Si el móvil no tiene voz, no pasa nada.
  static Future<void> say(String text) async {
    try {
      if (_ready != Lang.ttsLanguage) {
        await _tts.setLanguage(Lang.ttsLanguage);
        await _tts.setSpeechRate(0.5);
        await _tts.awaitSpeakCompletion(true);
        _ready = Lang.ttsLanguage;
      }
      await _tts.speak(text);
    } catch (_) {}
  }

  static Future<void> stop() async {
    try {
      await _tts.stop();
    } catch (_) {}
  }
}
