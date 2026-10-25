// Modelos de datos de Laia.

import '../i18n.dart';

Map<String, String> get kLanguages => Lang.en
    ? const {
        'es': 'Spanish',
        'en': 'English',
        'de': 'German',
        'fr': 'French',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ja': 'Japanese',
      }
    : const {
        'es': 'Español',
        'en': 'Inglés',
        'de': 'Alemán',
        'fr': 'Francés',
        'it': 'Italiano',
        'pt': 'Portugués',
        'ja': 'Japonés',
      };

const Map<String, String> kFlags = {
  'es': '🇪🇸',
  'en': '🇬🇧',
  'de': '🇩🇪',
  'fr': '🇫🇷',
  'it': '🇮🇹',
  'pt': '🇵🇹',
  'ja': '🇯🇵',
};

/// Bandera de un país a partir de su código ISO ("DE" -> 🇩🇪).
String flagOf(String countryCode) {
  final code = countryCode.toUpperCase();
  if (code.length != 2) return '🏳️';
  return String.fromCharCodes(code.codeUnits.map((c) => 0x1F1E6 + c - 65));
}

/// Tu cuenta, tal como la guarda el servidor.
class AppUser {
  final String id;
  final String email;
  final String name;
  final String address;
  final String phone;
  final bool isAdmin;
  final bool telegramLinked;

  const AppUser({
    required this.id,
    required this.email,
    this.name = '',
    this.address = '',
    this.phone = '',
    this.isAdmin = false,
    this.telegramLinked = false,
  });

  String get firstName => name.trim().isEmpty ? '' : name.trim().split(' ').first;

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
        id: j['id'].toString(),
        email: j['email'] as String? ?? '',
        name: j['name'] as String? ?? '',
        address: j['address'] as String? ?? '',
        phone: j['phone'] as String? ?? '',
        isAdmin: j['is_admin'] as bool? ?? false,
        telegramLinked: j['telegram_linked'] as bool? ?? false,
      );
}

/// Un negocio de tu lista. Laia solo llama a los verificados.
class Business {
  final String id;
  final String name;
  final String phone;
  final String country;
  final String language;
  final String address;
  final String status; // pendiente | verificado | rechazado
  final String source; // manual | google

  const Business({
    required this.id,
    required this.name,
    this.phone = '',
    this.country = '',
    this.language = 'es',
    this.address = '',
    this.status = 'pendiente',
    this.source = 'manual',
  });

  bool get isVerified => status == 'verificado';
  bool get isFromGoogle => source == 'google';
  bool get isAbroad => country.isNotEmpty && country != 'ES';

  factory Business.fromJson(Map<String, dynamic> j) => Business(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        phone: j['phone'] as String? ?? '',
        country: j['country'] as String? ?? '',
        language: j['language'] as String? ?? 'es',
        address: j['address'] as String? ?? '',
        status: j['status'] as String? ?? 'pendiente',
        source: j['source'] as String? ?? 'manual',
      );
}

/// Un sitio encontrado al buscar. Si viene de Google Maps se muestra, pero no se guarda.
class PlaceCandidate {
  final String name;
  final String address;
  final String country;
  final String language;
  final String? googlePlaceId;
  final String? businessId;
  final bool fromGoogle;

  const PlaceCandidate({
    required this.name,
    required this.address,
    required this.country,
    required this.language,
    this.googlePlaceId,
    this.businessId,
    this.fromGoogle = false,
  });

  factory PlaceCandidate.fromJson(Map<String, dynamic> j) => PlaceCandidate(
        name: j['name'] as String? ?? '',
        address: j['address'] as String? ?? '',
        country: j['country'] as String? ?? '',
        language: j['language'] as String? ?? 'es',
        googlePlaceId: j['google_place_id'] as String?,
        businessId: j['business_id'] as String?,
        fromGoogle: j['from_google'] as bool? ?? false,
      );

  /// Ya está en tu lista: se puede usar sin guardar nada más.
  Business? get asBusiness => businessId == null
      ? null
      : Business(
          id: businessId!,
          name: name,
          country: country,
          language: language,
          address: address,
          status: 'verificado',
          source: googlePlaceId == null ? 'manual' : 'google',
        );
}

/// Un país al que Laia puede llamar.
class Country {
  final String code;
  final String name;
  final String language;
  final String languageName;
  const Country(this.code, this.name, this.language, this.languageName);

  String get flag => flagOf(code);

  factory Country.fromJson(Map<String, dynamic> j) => Country(
        j['code'] as String? ?? '',
        j['name'] as String? ?? '',
        j['language'] as String? ?? 'en',
        j['language_name'] as String? ?? '',
      );
}

/// Lo que Laia ha entendido de tu orden, antes de llamar.
class OrderDraft {
  Business business;
  String mode; // pedido | reserva | consulta
  List<String> items;
  List<String> alternatives;
  double? maxPrice;
  String notes;
  bool askBeforeAlternative;

  OrderDraft({
    required this.business,
    this.mode = 'pedido',
    this.items = const [],
    this.alternatives = const [],
    this.maxPrice,
    this.notes = '',
    this.askBeforeAlternative = false,
  });

  factory OrderDraft.fromParse(Map<String, dynamic> j, Business business) => OrderDraft(
        business: business,
        mode: j['mode'] as String? ?? 'pedido',
        items: List<String>.from(j['items'] as List? ?? const []),
        alternatives: List<String>.from(j['alternatives'] as List? ?? const []),
        maxPrice: (j['max_price'] as num?)?.toDouble(),
        notes: j['notes'] as String? ?? '',
        askBeforeAlternative: j['ask_before_alternative'] as bool? ?? false,
      );

  Map<String, dynamic> toJson() => {
        'business_id': business.id,
        'mode': mode,
        'items': items,
        'alternatives': alternatives,
        'max_price': maxPrice,
        'notes': notes,
        'ask_before_alternative': askBeforeAlternative,
      };
}

/// Lo que ha entendido Gemma, antes de saber a qué negocio llamar.
class ParsedOrder {
  final Map<String, dynamic> raw;
  final Business? business;
  final String businessName;
  const ParsedOrder(this.raw, this.business, this.businessName);

  OrderDraft toDraft(Business business) => OrderDraft.fromParse(raw, business);
}

class TranscriptLine {
  final String who; // laia | negocio
  final String text;
  final String? translation; // al español, si el negocio habla otro idioma
  const TranscriptLine(this.who, this.text, [this.translation]);

  bool get isLaia => who == 'laia';
}

const kFinalStatuses = ['pedido_hecho', 'cancelado', 'fallido', 'pasada_a_ti'];

/// Un pedido en marcha o terminado, tal como lo devuelve el servidor.
class Order {
  final String id;
  final String status;
  final String businessName;
  final String language;
  final String languageName;
  final String mode;
  final List<String> items;
  final List<String> events;
  final List<TranscriptLine> transcript;
  final String? pendingQuestion;
  final Map<String, dynamic>? result;
  final DateTime? createdAt;

  const Order({
    required this.id,
    required this.status,
    required this.businessName,
    required this.language,
    required this.languageName,
    required this.mode,
    required this.items,
    required this.events,
    required this.transcript,
    this.pendingQuestion,
    this.result,
    this.createdAt,
  });

  bool get isFinished => kFinalStatuses.contains(status);
  bool get isForeign => language != 'es';

  factory Order.fromJson(Map<String, dynamic> j) => Order(
        id: j['id'].toString(),
        status: j['status'] as String? ?? '',
        businessName: j['business_name'] as String? ?? '',
        language: j['language'] as String? ?? 'es',
        languageName: j['language_name'] as String? ?? '',
        mode: j['mode'] as String? ?? 'pedido',
        items: List<String>.from(j['items'] as List? ?? const []),
        events: List<String>.from(j['events'] as List? ?? const []),
        transcript: [
          for (final t in (j['transcript'] as List? ?? const []))
            TranscriptLine(t['who'] as String? ?? '', t['text'] as String? ?? '', t['tr'] as String?),
        ],
        pendingQuestion: j['pending_question'] as String?,
        result: j['result'] as Map<String, dynamic>?,
        createdAt: DateTime.tryParse(j['created_at'] as String? ?? ''),
      );
}

Map<String, String> get kStatusLabels => {
  'llamando': t('Llamando', 'Calling'),
  'en_llamada': t('En llamada', 'On the call'),
  'esperando_tu_respuesta': t('Te necesita', 'Needs you'),
  'pedido_hecho': t('Hecho', 'Done'),
  'cancelado': t('No se hizo', 'Cancelled'),
  'fallido': t('No se pudo', 'Failed'),
  'pasada_a_ti': t('Te la pasé', 'Passed to you'),
};

Map<String, String> get kModeLabels => {
  'pedido': t('Pedir', 'Order'),
  'reserva': t('Reservar', 'Book'),
  'consulta': t('Preguntar', 'Ask'),
};
