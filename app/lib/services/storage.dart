import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';

/// Guarda en el móvil la dirección del servidor y tu sesión.
class Storage {
  static const _serverKey = 'laia_server';
  static const _tokenKey = 'laia_token';
  static const _introKey = 'laia_intro_seen';
  static const _handsFreeKey = 'laia_hands_free';

  static Future<bool> handsFree() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_handsFreeKey) ?? false;
  }

  static Future<void> setHandsFree(bool on) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_handsFreeKey, on);
  }

  static Future<bool> introSeen() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_introKey) ?? false;
  }

  static Future<void> setIntroSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_introKey, true);
  }

  static Future<String> serverUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_serverKey) ?? kDefaultServerUrl;
  }

  static Future<void> setServerUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_serverKey, url.trim());
  }

  static Future<String?> token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> setToken(String? token) async {
    final prefs = await SharedPreferences.getInstance();
    if (token == null) {
      await prefs.remove(_tokenKey);
    } else {
      await prefs.setString(_tokenKey, token);
    }
  }
}
