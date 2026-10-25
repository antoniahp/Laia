import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Idioma de la app: español o inglés. Se elige al entrar y se puede cambiar en Perfil.
class Lang {
  static const _key = 'laia_lang';
  static final current = ValueNotifier<String>('es');

  static bool get en => current.value == 'en';

  /// Para el reconocimiento de voz del móvil.
  static String get speechLocale => en ? 'en_US' : 'es_ES';

  /// Para la voz del móvil (modo manos libres).
  static String get ttsLanguage => en ? 'en-US' : 'es-ES';

  static Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      current.value = prefs.getString(_key) ?? 'es';
    } catch (_) {}
  }

  static Future<void> set(String lang) async {
    current.value = lang;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_key, lang);
    } catch (_) {}
  }
}

/// El texto en el idioma elegido: t('Hola', 'Hello').
String t(String es, String en) => Lang.en ? en : es;
