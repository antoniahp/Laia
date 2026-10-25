import 'package:flutter/services.dart';

/// Mantiene la pantalla encendida mientras el modo manos libres escucha.
class KeepScreenOn {
  static const _channel = MethodChannel('laia/screen');

  static Future<void> set(bool on) async {
    try {
      await _channel.invokeMethod('keepOn', {'on': on});
    } catch (_) {
      // Sin el código nativo (versiones antiguas) simplemente no hace nada
    }
  }
}
