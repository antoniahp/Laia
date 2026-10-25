import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_pcm_sound/flutter_pcm_sound.dart';

import 'api.dart';
import 'storage.dart';

/// Escucha la llamada en directo: el servidor manda el audio mezclado (negocio + Laia)
/// en PCM de 16 bits a 8 kHz y aquí se reproduce. No se graba nada.
class CallListener {
  static const _sampleRate = 8000;
  static const _prebufferBytes = 3200; // 200 ms de colchón para que no se corte

  WebSocket? _socket;
  StreamSubscription<dynamic>? _subscription;
  final List<int> _pending = [];
  bool _started = false;
  void Function()? onStopped;

  bool get isListening => _socket != null;

  Future<void> start(String orderId) async {
    if (isListening) return;
    final api = await LaiaApi.load();
    final token = await Storage.token();
    await FlutterPcmSound.setLogLevel(LogLevel.none);
    await FlutterPcmSound.setup(sampleRate: _sampleRate, channelCount: 1);
    final socket = await WebSocket.connect(
      api.listenUri(orderId).toString(),
      headers: {'Authorization': 'Bearer $token'},
    ).timeout(const Duration(seconds: 15));
    _socket = socket;
    _started = false;
    _pending.clear();
    _subscription = socket.listen(
      (data) {
        if (data is List<int>) _play(data);
      },
      onDone: () => stop(),
      onError: (Object _) => stop(),
      cancelOnError: true,
    );
  }

  void _play(List<int> data) {
    if (!_started) {
      _pending.addAll(data);
      if (_pending.length < _prebufferBytes) return;
      _started = true;
      _feed(Uint8List.fromList(_pending));
      _pending.clear();
      return;
    }
    _feed(Uint8List.fromList(data)); // copia propia: el plugin lee el buffer entero
  }

  void _feed(Uint8List bytes) {
    final even = bytes.length - bytes.length % 2;
    if (even == 0) return;
    final chunk = even == bytes.length ? bytes : Uint8List.fromList(bytes.sublist(0, even));
    FlutterPcmSound.feed(PcmArrayInt16(bytes: ByteData.sublistView(chunk)));
  }

  Future<void> stop() async {
    final socket = _socket;
    if (socket == null) return;
    _socket = null;
    await _subscription?.cancel();
    _subscription = null;
    try {
      await socket.close();
    } catch (_) {}
    try {
      await FlutterPcmSound.release();
    } catch (_) {}
    onStopped?.call();
  }
}
