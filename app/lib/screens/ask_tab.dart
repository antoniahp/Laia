import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../services/screen.dart';
import '../services/speaker.dart';
import '../services/storage.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/cta_button.dart';
import '../widgets/hands_free_confirm.dart';
import '../widgets/place_picker.dart';
import '../widgets/voice.dart';
import 'auth_screen.dart';
import 'businesses_screen.dart';
import 'call_screen.dart';
import 'profile_tab.dart';
import 'review_screen.dart';
import '../i18n.dart';

/// «Pedir»: dices qué quieres y dónde, Laia lo prepara.
class AskTab extends StatefulWidget {
  /// Solo la pestaña visible escucha en modo manos libres.
  final bool active;
  const AskTab({super.key, this.active = true});

  @override
  State<AskTab> createState() => _AskTabState();
}

class _AskTabState extends State<AskTab> {
  final _voice = VoiceInput();
  final _command = TextEditingController();

  AppUser? _user;
  List<Business> _mine = [];
  Order? _live;
  Business? _selected;
  bool _loading = true;
  bool _busy = false;

  // Manos libres: escucha sola mientras la app está abierta en «Pedir»
  bool _handsFree = false;
  bool _awaitingCommand = false; // ha oído «Laia» y espera la orden
  bool _isAway = false; // en otra pantalla (revisar, llamada...)
  String _heardText = ''; // lo último que ha oído, para ver que funciona
  Timer? _restart;
  Timer? _watchdog; // vuelve a escuchar si el móvil deja de hacerlo sin avisar
  bool _talking = false; // Laia está hablando: no escuchar para no oírse a sí misma

  static List<String> get _examples => [
    t('Pide una pizza cuatro quesos en Tres Hermanas. Si no hay, una margarita. Máximo 20 euros.',
        "Order a four-cheese pizza from Tres Hermanas. If they're out, a margherita. Max 20 euros."),
    t('Reserva mesa para 4 el sábado a las 21:00 en La Tagliatella', 'Book a table for 4 on Saturday at 9 pm at La Tagliatella'),
    t('Pregunta en la farmacia Gran Vía si tienen ibuprofeno infantil', "Ask the Gran Via pharmacy if they have children's ibuprofen"),
  ];

  @override
  void initState() {
    super.initState();
    _load();
    Storage.handsFree().then((on) {
      if (!mounted) return;
      setState(() => _handsFree = on);
      _scheduleListen(const Duration(milliseconds: 600));
    });
    // Android a veces corta el micro sin avisar (errores del reconocedor, llamadas, el sistema...).
    // Cada 3 s: si debería estar escuchando y no lo está, vuelve a empezar.
    _watchdog = Timer.periodic(const Duration(seconds: 3), (_) {
      if (!_canListenHandsFree || _talking) return;
      _voice.forgetIfStopped();
      if (!_voice.listening) _listenHandsFree();
    });
  }

  @override
  void didUpdateWidget(AskTab old) {
    super.didUpdateWidget(old);
    if (old.active != widget.active) {
      if (widget.active) {
        _scheduleListen(const Duration(milliseconds: 400));
      } else {
        _restart?.cancel();
        KeepScreenOn.set(false);
        _voice.stop(_refresh);
      }
    }
  }

  @override
  void dispose() {
    _watchdog?.cancel();
    _restart?.cancel();
    _silence?.cancel();
    KeepScreenOn.set(false);
    _voice.dispose();
    _command.dispose();
    super.dispose();
  }

  void _refresh() {
    if (mounted) setState(() {});
  }

  bool get _canListenHandsFree => mounted && _handsFree && widget.active && !_isAway && !_busy && !_loading;

  void _scheduleListen([Duration delay = const Duration(milliseconds: 350)]) {
    _restart?.cancel();
    KeepScreenOn.set(_handsFree && widget.active);
    if (!_handsFree) return;
    _restart = Timer(delay, _listenHandsFree);
  }

  // El reconocedor corta en cada pausa: juntamos los trozos y decidimos tras ~2 s de silencio
  String _said = ''; // trozos ya terminados
  String _saying = ''; // lo que está oyendo ahora
  Timer? _silence;

  String get _phrase => '$_said $_saying'.trim();

  Future<void> _listenHandsFree() async {
    _voice.forgetIfStopped();
    if (!_canListenHandsFree || _talking || _voice.listening) return;
    _saying = '';
    final error = await _voice.listenOnce(
      onChange: _refresh,
      onStopped: () {
        _keepPiece();
        _scheduleListen(const Duration(milliseconds: 150));
      },
      onResult: (text, isFinal) {
        _saying = text;
        if (isFinal) _keepPiece();
        if (!mounted) return;
        setState(() => _heardText = _phrase);
        final after = VoiceInput.afterWakeWord(_phrase);
        if (_awaitingCommand || after != null) {
          setState(() => _command.text = _awaitingCommand ? VoiceInput.clean(_phrase) : after!);
        }
        // Con la orden ya dicha, espera 5 s por si añades algo; si solo has dicho «Oye Laia», contesta antes
        final hasOrder = _awaitingCommand ? VoiceInput.clean(_phrase).isNotEmpty : (after?.isNotEmpty ?? false);
        _silence?.cancel();
        _silence = Timer(Duration(milliseconds: hasOrder ? 5000 : 1500), _decide);
      },
    );
    if (error != null && mounted) {
      setState(() => _handsFree = false);
      showSnack(context, error);
    }
  }

  void _keepPiece() {
    if (_saying.trim().isEmpty) return;
    _said = '$_said ${_saying.trim()}'.trim();
    _saying = '';
  }

  /// Tras un silencio: ¿era para Laia? ¿ya tenemos la orden?
  void _decide() {
    if (!mounted || _busy) return;
    _keepPiece();
    final phrase = _said;
    _said = '';
    if (phrase.isEmpty) return;
    if (_awaitingCommand) {
      final command = VoiceInput.clean(phrase);
      if (command.isEmpty) return;
      setState(() => _command.text = command);
      _heard();
      return;
    }
    final after = VoiceInput.afterWakeWord(phrase);
    if (after == null) return; // no ha dicho «Laia»: no era para ella
    if (after.isEmpty) {
      HapticFeedback.mediumImpact();
      setState(() => _awaitingCommand = true); // «Oye Laia»… y ahora la orden
      _answerOutLoud(t('¿Sí? Dime qué quieres.', 'Yes? Tell me what you want.'));
    } else {
      setState(() => _command.text = after);
      _heard();
    }
  }

  /// Laia contesta en voz alta sin oírse a sí misma.
  Future<void> _answerOutLoud(String text) async {
    _restart?.cancel();
    _talking = true;
    await _voice.stop(_refresh);
    await Speaker.say(text);
    _talking = false;
    _scheduleListen(const Duration(milliseconds: 100));
  }

  void _heard() {
    _awaitingCommand = false;
    HapticFeedback.heavyImpact();
    _voice.stop(_refresh);
    _prepare(handsFree: true);
  }

  Future<void> _toggleHandsFree(bool on) async {
    await Storage.setHandsFree(on);
    setState(() {
      _handsFree = on;
      _awaitingCommand = false;
    });
    if (on) {
      _scheduleListen(const Duration(milliseconds: 200));
    } else {
      _restart?.cancel();
      KeepScreenOn.set(false);
      await _voice.stop(_refresh);
    }
  }

  /// Mientras otra pantalla está encima, no escucha.
  Future<T?> _away<T>(Future<T?> Function() open) async {
    _restart?.cancel();
    await _voice.stop(_refresh);
    _isAway = true;
    try {
      return await open();
    } finally {
      _isAway = false;
      _scheduleListen(const Duration(milliseconds: 500));
    }
  }

  Future<void> _load() async {
    try {
      final api = await LaiaApi.load();
      final results = await Future.wait([api.me(), api.businesses(), api.orders()]);
      if (!mounted) return;
      final orders = results[2] as List<Order>;
      setState(() {
        _user = results[0] as AppUser;
        _mine = (results[1] as List<Business>).where((b) => b.isVerified && !b.isAbroad).toList();
        _live = orders.where((o) => !o.isFinished).firstOrNull;
        if (_selected != null && !_mine.any((b) => b.id == _selected!.id)) _selected = null;
        _loading = false;
      });
      _scheduleListen();
    } on ApiException catch (e) {
      if (e.status == 401) return _logout();
      if (!mounted) return;
      setState(() => _loading = false);
      showSnack(context, e.message);
    }
  }

  Future<void> _logout() async {
    await Storage.setToken(null);
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => const AuthScreen()), (_) => false);
  }

  Future<void> _mic() async {
    if (_handsFree) {
      // En manos libres el micro ya escucha: tocarlo es «te hablo ya», sin decir «Laia»
      if (!_voice.listening) _listenHandsFree();
      setState(() => _awaitingCommand = true);
      HapticFeedback.selectionClick();
      return;
    }
    if (_voice.listening) {
      await _voice.stop(_refresh);
      return;
    }
    // Un toque y hablas: al callarte, Laia prepara el pedido sola (sin pulsar «Preparar»)
    var done = false;
    final error = await _voice.listenOnce(
      onChange: _refresh,
      onResult: (text, isFinal) {
        if (mounted) setState(() => _command.text = VoiceInput.clean(text));
      },
      onStopped: () {
        if (done || !mounted || _busy) return;
        done = true;
        if (_command.text.trim().isNotEmpty) _prepare(handsFree: true);
      },
    );
    if (error != null && mounted) showSnack(context, error);
  }

  Future<void> _prepare({bool handsFree = false}) async {
    final command = _command.text.trim();
    if (command.isEmpty) {
      showSnack(context, t('Dime qué quieres: toca el micro o escríbelo.', 'Tell me what you want: tap the mic or type it.'));
      return;
    }
    setState(() => _busy = true);
    await _voice.stop(_refresh);
    try {
      final api = await LaiaApi.load();
      final parsed = await api.parse(command, _selected);
      if (!mounted) return;
      var business = parsed.business;
      if (business == null) {
        if (parsed.businessName.trim().isEmpty) {
          showSnack(context, t('¿A qué sitio llamo? Dilo en la frase («…en Tres Hermanas») o elige uno de tus sitios.', 'Which place should I call? Say it ("…at Tres Hermanas") or pick one of your places.'));
          return;
        }
        business = handsFree ? await _findQuietly(api, parsed.businessName) : null;
        if (!mounted) return;
        business ??= await _away(() => pickPlace(context, parsed.businessName));
      }
      if (business == null || !mounted) return;
      final user = _user ?? await api.me();
      if (!mounted) return;
      final chosen = business;
      final draft = parsed.toDraft(chosen);
      if (handsFree && draft.items.isNotEmpty) {
        // Sin tocar nada: cuenta atrás y llama sola, salvo que digas «no»
        final go = await _away(() => confirmHandsFree(context, draft));
        if (go != true || !mounted) return;
        final order = await api.createOrder(draft);
        if (!mounted) return;
        _command.clear();
        _selected = null;
        await _away(() => Navigator.push(context, MaterialPageRoute(builder: (_) => CallScreen(orderId: order.id))));
        await _load();
        return;
      }
      final placed = await _away(
        () => Navigator.push<bool>(
          context,
          MaterialPageRoute(builder: (_) => ReviewScreen(user: user, draft: draft)),
        ),
      );
      if (placed == true) {
        _command.clear();
        _selected = null;
      }
      await _load();
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
      _scheduleListen(const Duration(milliseconds: 800));
    }
  }

  /// Manos libres: si el sitio es inequívoco (uno guardado, o un único resultado), lo elige sin preguntar.
  Future<Business?> _findQuietly(LaiaApi api, String name) async {
    final found = await api.searchPlaces(name);
    final saved = found.where((p) => p.businessId != null).toList();
    final only = saved.length == 1 ? saved.first : (found.length == 1 ? found.first : null);
    if (only == null) return null;
    return only.asBusiness ?? await api.addPlace(only.googlePlaceId!, name);
  }

  Future<void> _openMyPlaces() async {
    final picked = await _away(
      () => Navigator.push<Business>(
        context,
        MaterialPageRoute(builder: (_) => const BusinessesScreen(pickMode: true)),
      ),
    );
    await _load();
    if (picked != null && mounted) setState(() => _selected = picked);
  }

  Future<void> _openProfile() async {
    await _away(() => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfilePage())));
    await _load();
  }

  String get _statusText {
    if (!_handsFree) return _voice.listening ? t('Te escucho…', 'Listening…') : t('Toca y habla', 'Tap and talk');
    if (_busy) return t('Laia está pensando…', 'Laia is thinking…');
    if (_awaitingCommand) return t('Dime qué quieres…', 'Tell me what you want…');
    return _voice.listening ? t('Di «Oye Laia» y tu pedido', 'Say "Hey Laia" and your order') : t('Manos libres activado', 'Hands-free on');
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final scheme = Theme.of(context).colorScheme;
    final user = _user;
    final hello = (user?.firstName.isNotEmpty ?? false) ? t('Hola, ${user!.firstName}', 'Hi, ${user.firstName}') : t('Hola', 'Hi');
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          GradientHeader(
            title: t('$hello 👋\n¿Qué te pido?', '$hello 👋\nWhat can I get you?'),
            subtitle: t('Dímelo con tu voz: qué quieres, dónde y tus reglas.', 'Say it out loud: what you want, where and your rules.'),
            gradient: LaiaColors.brandGradient,
          ),
          if (_live != null) ...[
            const SizedBox(height: 12),
            _LiveCallCard(
              order: _live!,
              onTap: () async {
                await _away(
                  () => Navigator.push(context, MaterialPageRoute(builder: (_) => CallScreen(orderId: _live!.id))),
                );
                await _load();
              },
            ),
          ],
          if (user != null && user.address.isEmpty) ...[
            const SizedBox(height: 12),
            TipCard(
              icon: Icons.home_outlined,
              title: t('Añade tu dirección', 'Add your address'),
              text: t('Laia la necesita para pedirte comida a domicilio.', 'Laia needs it to order food delivery for you.'),
              onTap: _openProfile,
            ),
          ] else if (user != null && user.phone.isEmpty) ...[
            const SizedBox(height: 12),
            TipCard(
              icon: Icons.phone_outlined,
              title: t('Añade tu teléfono', 'Add your phone'),
              text: t('Para el repartidor y para que Laia te pueda pasar la llamada.', 'For the courier and so Laia can pass you the call.'),
              onTap: _openProfile,
            ),
          ],
          const SizedBox(height: 28),
          Center(child: MicButton(listening: _voice.listening, onTap: _mic)),
          const SizedBox(height: 14),
          Center(
            child: Text(
              _statusText,
              textAlign: TextAlign.center,
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
          if (_handsFree && _heardText.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                t('Oigo: «$_heardText»', 'I hear: "$_heardText"'),
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13, fontStyle: FontStyle.italic),
              ),
            ),
          const SizedBox(height: 10),
          Center(
            child: Material(
              color: _handsFree ? scheme.tertiaryContainer : scheme.surface,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(28),
                side: BorderSide(color: _handsFree ? scheme.tertiary : scheme.outline),
              ),
              child: InkWell(
                borderRadius: BorderRadius.circular(28),
                onTap: () => _toggleHandsFree(!_handsFree),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 4, 6, 4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.hearing, size: 20, color: _handsFree ? scheme.onTertiaryContainer : scheme.onSurfaceVariant),
                      const SizedBox(width: 8),
                      Text(
                        t('Manos libres: «Oye Laia»', 'Hands-free: "Hey Laia"'),
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: _handsFree ? scheme.onTertiaryContainer : scheme.onSurface,
                        ),
                      ),
                      Switch(value: _handsFree, onChanged: _toggleHandsFree),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _command,
            minLines: 2,
            maxLines: 5,
            textCapitalization: TextCapitalization.sentences,
            decoration: InputDecoration(
              labelText: t('Tu orden', 'Your request'),
              hintText: _examples.first,
              suffixIcon: _command.text.isEmpty
                  ? null
                  : IconButton(
                      tooltip: t('Borrar', 'Clear'),
                      icon: const Icon(Icons.close),
                      onPressed: () => setState(() => _command.clear()),
                    ),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 12),
          _PlaceRow(
            mine: _mine,
            selected: _selected,
            onSelect: (b) => setState(() => _selected = b),
            onMore: _openMyPlaces,
          ),
          const SizedBox(height: 20),
          CtaButton(
            label: _busy ? t('Laia está pensando…', 'Laia is thinking…') : t('Preparar llamada', 'Prepare call'),
            icon: Icons.auto_awesome,
            busy: _busy,
            onPressed: _prepare,
          ),
          const SizedBox(height: 28),
          SectionTitle(t('Prueba a decir', 'Try saying')),
          for (final e in _examples)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Material(
                color: scheme.surface,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: BorderSide(color: scheme.outlineVariant),
                ),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: () => setState(() => _command.text = e),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        Icon(Icons.format_quote_rounded, color: scheme.secondary),
                        const SizedBox(width: 10),
                        Expanded(child: Text(e)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _PlaceRow extends StatelessWidget {
  final List<Business> mine;
  final Business? selected;
  final ValueChanged<Business?> onSelect;
  final VoidCallback onMore;
  const _PlaceRow({required this.mine, required this.selected, required this.onSelect, required this.onMore});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final shown = [...mine.take(6)];
    if (selected != null && !shown.any((b) => b.id == selected!.id)) shown.insert(0, selected!);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          selected == null
              ? t('Di el sitio en la frase, o elige uno de los tuyos:', 'Say the place, or pick one of yours:')
              : t('Laia llamará a ${selected!.name}', 'Laia will call ${selected!.name}'),
          style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final b in shown)
              ChoiceChip(
                label: Text(b.name),
                selected: selected?.id == b.id,
                onSelected: (on) => onSelect(on ? b : null),
              ),
            ActionChip(
              avatar: Icon(Icons.storefront_outlined, size: 18, color: scheme.primary),
              label: Text(t('Mis sitios', 'My places')),
              onPressed: onMore,
            ),
          ],
        ),
      ],
    );
  }
}

class _LiveCallCard extends StatelessWidget {
  final Order order;
  final VoidCallback onTap;
  const _LiveCallCard({required this.order, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final needsYou = order.pendingQuestion != null;
    return Material(
      color: needsYou ? LaiaColors.orangeDeep : LaiaColors.teal,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(needsYou ? Icons.notifications_active : Icons.phone_in_talk, color: Colors.white, size: 30),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      needsYou ? t('Laia te necesita', 'Laia needs you') : t('Llamada en curso', 'Call in progress'),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16),
                    ),
                    Text(
                      needsYou ? order.pendingQuestion! : t('${order.businessName} · toca para escucharla', '${order.businessName} · tap to listen'),
                      style: const TextStyle(color: Colors.white),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.white),
            ],
          ),
        ),
      ),
    );
  }
}
