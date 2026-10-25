import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/models.dart';
import 'storage.dart';
import '../i18n.dart';

class ApiException implements Exception {
  final String message;
  final int status;
  ApiException(this.message, [this.status = 0]);
  @override
  String toString() => message;
}

/// Habla con el servidor de Laia.
class LaiaApi {
  final String serverUrl;
  final String? token;
  LaiaApi(this.serverUrl, [this.token]);

  /// Crea el cliente con lo guardado en el móvil.
  static Future<LaiaApi> load() async => LaiaApi(await Storage.serverUrl(), await Storage.token());

  Uri _uri(String path) {
    final base = serverUrl.endsWith('/') ? serverUrl.substring(0, serverUrl.length - 1) : serverUrl;
    return Uri.parse('$base$path');
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept-Language': Lang.current.value,
        if (token != null) 'Authorization': 'Bearer $token',
      };

  dynamic _handle(http.Response r) {
    final body = utf8.decode(r.bodyBytes);
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return body.isEmpty ? null : jsonDecode(body);
    }
    String msg = 'Error ${r.statusCode}';
    try {
      final j = jsonDecode(body);
      final detail = j is Map ? j['detail'] : null;
      if (detail is String) {
        msg = detail;
      } else if (detail is List && detail.isNotEmpty) {
        msg = t('Revisa los datos: ', 'Check your details: ') + (detail.first['msg'] ?? '').toString();
      }
    } catch (_) {}
    throw ApiException(msg, r.statusCode);
  }

  Future<dynamic> _send(String method, String path, [Map<String, dynamic>? body]) async {
    try {
      final req = http.Request(method, _uri(path))..headers.addAll(_headers);
      if (body != null) req.body = jsonEncode(body);
      // Render en plan gratis puede tardar en despertar: margen amplio
      final streamed = await req.send().timeout(const Duration(seconds: 60));
      return _handle(await http.Response.fromStream(streamed));
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException(t('No puedo conectar con Laia. Revisa tu conexión e inténtalo otra vez.', "I can't reach Laia. Check your connection and try again."));
    }
  }

  // ---------- cuentas ----------

  Future<(String, AppUser)> register(String email, String password, String name, String code, bool acceptTerms) async {
    final j = await _send('POST', '/api/auth/register', {
      'email': email,
      'password': password,
      'name': name,
      'signup_code': code,
      'accept_terms': acceptTerms,
    });
    return (j['token'] as String, AppUser.fromJson(j['user'] as Map<String, dynamic>));
  }

  Future<(String, AppUser)> login(String email, String password) async {
    final j = await _send('POST', '/api/auth/login', {'email': email, 'password': password});
    return (j['token'] as String, AppUser.fromJson(j['user'] as Map<String, dynamic>));
  }

  Future<AppUser> me() async => AppUser.fromJson(await _send('GET', '/api/me') as Map<String, dynamic>);

  Future<AppUser> updateMe({String? name, String? address, String? phone}) async {
    final j = await _send('PATCH', '/api/me', {
      if (name != null) 'name': name,
      if (address != null) 'address': address,
      if (phone != null) 'phone': phone,
    });
    return AppUser.fromJson(j as Map<String, dynamic>);
  }

  Future<String> telegramLink() async {
    final j = await _send('POST', '/api/me/telegram');
    return j['url'] as String;
  }

  /// Todo lo que Laia guarda de ti, en JSON bonito.
  Future<String> exportMyData() async {
    final j = await _send('GET', '/api/me/export');
    return const JsonEncoder.withIndent('  ').convert(j);
  }

  Future<void> deleteAccount() async => _send('DELETE', '/api/me');

  /// Página legal pública (privacidad, terminos, negocios).
  Uri legalPage(String page) => _uri('/legal/$page/');

  // ---------- negocios ----------

  Future<List<Business>> businesses([String query = '']) async {
    final j = await _send('GET', '/api/businesses?q=${Uri.encodeQueryComponent(query)}') as List;
    return [for (final b in j) Business.fromJson(b as Map<String, dynamic>)];
  }

  Future<Business> proposeBusiness(String name, String phone, String language, String city) async {
    final j = await _send('POST', '/api/businesses', {
      'name': name,
      'phone': phone,
      'language': language,
      'city': city,
    });
    return Business.fromJson(j as Map<String, dynamic>);
  }

  // ---------- pedidos ----------

  /// Gemma entiende la orden. Si no le pasas negocio, te dice el nombre del sitio que has dicho.
  Future<ParsedOrder> parse(String command, Business? business) async {
    final j = await _send('POST', '/api/parse', {
      'command': command,
      if (business != null) 'business_id': business.id,
    }) as Map<String, dynamic>;
    final b = j['business'];
    return ParsedOrder(
      j,
      b == null ? null : Business.fromJson(b as Map<String, dynamic>),
      j['business_name'] as String? ?? '',
    );
  }

  /// Busca un sitio: en tu lista y en Google Maps (cerca de ti, o en [country]). No guarda nada.
  Future<List<PlaceCandidate>> searchPlaces(String search, {String country = ''}) async {
    final j = await _send('POST', '/api/places/search', {'search': search, 'country': country}) as List;
    return [for (final p in j) PlaceCandidate.fromJson(p as Map<String, dynamic>)];
  }

  /// Guarda en tu lista el sitio de Google Maps elegido (solo su identificador).
  Future<Business> addPlace(String googlePlaceId, String label) async {
    final j = await _send('POST', '/api/places/add', {'google_place_id': googlePlaceId, 'label': label});
    return Business.fromJson(j as Map<String, dynamic>);
  }

  Future<List<Country>> countries() async {
    final j = await _send('GET', '/api/places/countries') as List;
    return [for (final c in j) Country.fromJson(c as Map<String, dynamic>)];
  }

  Future<Order> createOrder(OrderDraft draft) async =>
      Order.fromJson(await _send('POST', '/api/orders', draft.toJson()) as Map<String, dynamic>);

  Future<List<Order>> orders() async {
    final j = await _send('GET', '/api/orders') as List;
    return [for (final o in j) Order.fromJson(o as Map<String, dynamic>)];
  }

  Future<Order> getOrder(String id) async =>
      Order.fromJson(await _send('GET', '/api/orders/$id') as Map<String, dynamic>);

  Future<Order> answer(String id, String answer) async =>
      Order.fromJson(await _send('POST', '/api/orders/$id/answer', {'answer': answer}) as Map<String, dynamic>);

  Future<Order> hangup(String id) async =>
      Order.fromJson(await _send('POST', '/api/orders/$id/hangup') as Map<String, dynamic>);

  /// «Hablar yo»: Laia pasa la llamada a tu móvil.
  Future<Order> transfer(String id) async =>
      Order.fromJson(await _send('POST', '/api/orders/$id/transfer') as Map<String, dynamic>);

  /// Dirección websocket para escuchar la llamada en directo.
  Uri listenUri(String orderId) {
    final http = _uri('/ws/app/listen/$orderId');
    return http.replace(scheme: http.scheme == 'https' ? 'wss' : 'ws');
  }
}
