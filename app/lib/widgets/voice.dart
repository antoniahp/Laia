import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../i18n.dart';
import '../services/wake_word.dart';
import '../theme.dart';

/// Dictado en español. Lo usan «Pedir» y «Extranjero».
class VoiceInput {
  final _speech = SpeechToText();
  bool _ready = false;
  bool listening = false;

  Future<bool> _init(VoidCallback onChange) async {
    if (_ready) return true;
    _ready = await _speech.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          listening = false;
          onChange();
          _onStopped?.call();
        }
      },
      onError: (_) {
        listening = false;
        onChange();
        _onStopped?.call();
      },
    );
    return _ready;
  }

  VoidCallback? _onStopped;

  /// Empieza o para de escuchar. Devuelve un mensaje de error si no se puede usar el micrófono.
  Future<String?> toggle({required void Function(String text) onText, required VoidCallback onChange}) async {
    if (listening) {
      await stop(onChange);
      return null;
    }
    _onStopped = null;
    if (!await _init(onChange)) return _micError;
    await _listen(onText: (r) => onText(clean(r.recognizedWords)), onChange: onChange);
    return null;
  }

  /// Una escucha para el modo manos libres: avisa con cada resultado y cuando termina.
  Future<String?> listenOnce({
    required void Function(String text, bool isFinal) onResult,
    required VoidCallback onChange,
    required VoidCallback onStopped,
  }) async {
    if (!await _init(onChange)) return _micError;
    if (listening) return null;
    _onStopped = onStopped;
    await _listen(onText: (r) => onResult(r.recognizedWords, r.finalResult), onChange: onChange, long: true);
    return null;
  }

  Future<void> _listen({
    required void Function(SpeechRecognitionResult r) onText,
    required VoidCallback onChange,
    bool long = false,
  }) async {
    listening = true;
    onChange();
    await _speech.listen(
      onResult: onText,
      listenOptions: SpeechListenOptions(
        localeId: Lang.speechLocale,
        listenFor: long ? const Duration(seconds: 50) : null,
        pauseFor: Duration(seconds: long ? 4 : 5),
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.dictation,
      ),
    );
  }

  Future<void> stop([VoidCallback? onChange]) async {
    _onStopped = null;
    if (listening) await _speech.stop();
    listening = false;
    onChange?.call();
  }

  static String get _micError => t('No puedo usar el micrófono. Revisa los permisos de Laia en Ajustes del móvil.', "I can't use the microphone. Check Laia's permissions in your phone settings.");

  /// Quita el «oye Laia» del principio.
  static String clean(String text) => WakeWord.clean(text);

  /// Si la frase llama a Laia, devuelve lo que viene después (puede ser vacío). Si no, null.
  static String? afterWakeWord(String text) => WakeWord.after(text);

  void dispose() {
    _onStopped = null;
    _speech.cancel();
  }
}

/// El botón grande del micrófono.
class MicButton extends StatelessWidget {
  final bool listening;
  final VoidCallback onTap;
  final double size;
  final Gradient gradient;
  const MicButton({
    super.key,
    required this.listening,
    required this.onTap,
    this.size = 128,
    this.gradient = LaiaColors.micGradient,
  });

  @override
  Widget build(BuildContext context) {
    final grown = listening ? size * 1.12 : size;
    return Semantics(
      button: true,
      label: listening ? t('Dejar de escuchar', 'Stop listening') : t('Hablar con Laia', 'Talk to Laia'),
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 260),
          curve: Curves.easeOut,
          width: grown,
          height: grown,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: listening
                ? const LinearGradient(colors: [Color(0xFFEF4444), LaiaColors.red])
                : gradient,
            boxShadow: [
              BoxShadow(
                color: (listening ? LaiaColors.red : LaiaColors.orange).withValues(alpha: 0.38),
                blurRadius: listening ? 44 : 26,
                spreadRadius: listening ? 10 : 2,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Icon(listening ? Icons.stop_rounded : Icons.mic_rounded, size: size * 0.44, color: Colors.white),
        ),
      ),
    );
  }
}
