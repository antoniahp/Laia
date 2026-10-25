import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../services/call_listener.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../i18n.dart';

/// La llamada en directo: escuchar, responder a Laia, hablar tú o colgar.
class CallScreen extends StatefulWidget {
  final String orderId;
  const CallScreen({super.key, required this.orderId});

  @override
  State<CallScreen> createState() => _CallScreenState();
}

class _CallScreenState extends State<CallScreen> {
  final _answer = TextEditingController();
  final _scroll = ScrollController();
  final _listener = CallListener();
  LaiaApi? _api;
  Timer? _timer;
  Order? _order;
  String? _lastQuestion;
  int _lastLines = 0;
  bool _sending = false;
  bool _connecting = false;
  bool _acting = false;
  bool _showOriginal = false;

  @override
  void initState() {
    super.initState();
    _listener.onStopped = () {
      if (mounted) setState(() {});
    };
    _refresh();
    _timer = Timer.periodic(const Duration(milliseconds: 1500), (_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    _listener.onStopped = null;
    _listener.stop();
    _answer.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<LaiaApi> get _client async => _api ??= await LaiaApi.load();

  Future<void> _refresh() async {
    try {
      final o = await (await _client).getOrder(widget.orderId);
      if (!mounted) return;
      _apply(o);
    } catch (_) {
      // reintenta en el siguiente ciclo
    }
  }

  void _apply(Order o) {
    if (o.pendingQuestion != null && o.pendingQuestion != _lastQuestion) {
      HapticFeedback.heavyImpact(); // Laia te necesita
    }
    _lastQuestion = o.pendingQuestion;
    final grew = o.transcript.length > _lastLines;
    _lastLines = o.transcript.length;
    setState(() => _order = o);
    if (o.isFinished) {
      _timer?.cancel();
      _listener.stop();
    }
    if (grew) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scroll.hasClients) {
          _scroll.animateTo(_scroll.position.maxScrollExtent,
              duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
        }
      });
    }
  }

  Future<void> _send(String text) async {
    if (text.trim().isEmpty) return;
    setState(() => _sending = true);
    try {
      final o = await (await _client).answer(widget.orderId, text.trim());
      _answer.clear();
      if (mounted) _apply(o);
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _toggleListen() async {
    if (_listener.isListening) {
      await _listener.stop();
      return;
    }
    setState(() => _connecting = true);
    try {
      await _listener.start(widget.orderId);
    } catch (_) {
      if (mounted) showSnack(context, t('No puedo conectar el audio ahora. Sigue la conversación por escrito.', 'I can\'t connect the audio right now. Follow the conversation in text.'));
    } finally {
      if (mounted) setState(() => _connecting = false);
    }
  }

  Future<void> _hangup() async {
    final ok = await _confirm(t('¿Colgar?', 'Hang up?'), t('Laia colgará y no se hará el pedido.', 'Laia will hang up and the order won\'t be placed.'), t('Colgar', 'Hang up'));
    if (!ok) return;
    setState(() => _acting = true);
    try {
      final o = await (await _client).hangup(widget.orderId);
      if (mounted) _apply(o);
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  /// «Hablar yo»: Laia avisa al negocio y te llama a tu móvil para que sigas tú.
  Future<void> _talkMyself() async {
    final api = await _client;
    var user = await api.me();
    if (!mounted) return;
    if (user.phone.isEmpty) {
      final phone = await _askPhone();
      if (phone == null || phone.isEmpty) return;
      try {
        user = await api.updateMe(phone: phone);
      } on ApiException catch (e) {
        if (mounted) showSnack(context, e.message);
        return;
      }
    }
    final ok = await _confirm(
      t('¿Hablas tú?', 'Want to talk?'),
      t('Laia avisará al negocio y te llamará al ${user.phone}. Contesta y seguirás tú la conversación.', 'Laia will tell the business and call you at ${user.phone}. Answer and you take over.'),
      t('Pásamela', 'Pass it to me'),
    );
    if (!ok) return;
    setState(() => _acting = true);
    try {
      await _listener.stop(); // si no, te oirías dos veces
      final o = await api.transfer(widget.orderId);
      if (mounted) {
        _apply(o);
        showSnack(context, t('Te está llamando: contesta en tu móvil.', 'She\'s calling you: answer your phone.'));
      }
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _acting = false);
    }
  }

  Future<String?> _askPhone() {
    final controller = TextEditingController(text: '+34 ');
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t('¿A qué móvil te llamo?', 'Which phone should I call?')),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: TextInputType.phone,
          decoration: InputDecoration(labelText: t('Tu teléfono', 'Your phone')),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(t('Cancelar', 'Cancel'))),
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: Text(t('Guardar', 'Save')),
          ),
        ],
      ),
    ).whenComplete(controller.dispose);
  }

  Future<bool> _confirm(String title, String text, String action) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(text),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
          FilledButton(
            style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
            onPressed: () => Navigator.pop(context, true),
            child: Text(action),
          ),
        ],
      ),
    );
    return ok ?? false;
  }

  @override
  Widget build(BuildContext context) {
    final o = _order;
    return Scaffold(
      appBar: AppBar(title: Text(o?.businessName ?? t('Llamada', 'Call'))),
      body: o == null
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: Column(
                children: [
                  Expanded(
                    child: ListView(
                      controller: _scroll,
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                      children: [
                        _CallHeader(order: o, listening: _listener.isListening),
                        if (!o.isFinished) ...[
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: _RoundAction(
                                  icon: _listener.isListening ? Icons.headset_off : Icons.headphones,
                                  label: _connecting
                                      ? t('Conectando…', 'Connecting…')
                                      : (_listener.isListening ? t('Dejar de oír', 'Stop listening') : t('Escuchar', 'Listen')),
                                  color: LaiaColors.indigo,
                                  active: _listener.isListening,
                                  onTap: _connecting ? null : _toggleListen,
                                ),
                              ),
                              Expanded(
                                child: _RoundAction(
                                  icon: Icons.phone_forwarded,
                                  label: t('Hablar yo', 'Let me talk'),
                                  color: LaiaColors.teal,
                                  onTap: _acting ? null : _talkMyself,
                                ),
                              ),
                              Expanded(
                                child: _RoundAction(
                                  icon: Icons.call_end,
                                  label: t('Colgar', 'Hang up'),
                                  color: LaiaColors.red,
                                  onTap: _acting ? null : _hangup,
                                ),
                              ),
                            ],
                          ),
                        ],
                        if (o.pendingQuestion != null) ...[
                          const SizedBox(height: 16),
                          _QuestionCard(
                            question: o.pendingQuestion!,
                            controller: _answer,
                            sending: _sending,
                            onSend: _send,
                          ),
                        ],
                        if (o.result != null) ...[
                          const SizedBox(height: 16),
                          _ResultCard(order: o),
                        ],
                        const SizedBox(height: 22),
                        Row(
                          children: [
                            Expanded(
                              child: SectionTitle(o.transcript.isEmpty ? t('Conversación', 'Conversation') : t('Conversación · ${o.languageName}', 'Conversation · ${o.languageName}')),
                            ),
                            if (o.isForeign && o.transcript.isNotEmpty)
                              TextButton(
                                onPressed: () => setState(() => _showOriginal = !_showOriginal),
                                child: Text(_showOriginal ? t('Ver en español', 'See translation') : t('Ver original', 'See original')),
                              ),
                          ],
                        ),
                        if (o.transcript.isEmpty)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: Text(
                              o.isFinished ? t('No hubo conversación.', 'There was no conversation.') : t('Aquí verás lo que se dice, frase a frase.', 'You\'ll see what\'s said here, line by line.'),
                              style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
                            ),
                          ),
                        for (final line in o.transcript) _Bubble(line: line, showOriginal: _showOriginal || !o.isForeign),
                        const SizedBox(height: 12),
                        _Events(events: o.events),
                      ],
                    ),
                  ),
                  if (o.isFinished)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                      child: FilledButton(onPressed: () => Navigator.pop(context), child: Text(t('Listo', 'Done'))),
                    ),
                ],
              ),
            ),
    );
  }
}

class _CallHeader extends StatelessWidget {
  final Order order;
  final bool listening;
  const _CallHeader({required this.order, required this.listening});

  @override
  Widget build(BuildContext context) {
    final (IconData icon, String label) = switch (order.status) {
      'llamando' => (Icons.ring_volume, t('Llamando…', 'Calling…')),
      'en_llamada' => (Icons.record_voice_over, t('Laia está hablando', 'Laia is talking')),
      'esperando_tu_respuesta' => (Icons.notifications_active, t('Laia te necesita', 'Laia needs you')),
      'pedido_hecho' => (Icons.check_circle, order.mode == 'reserva' ? t('¡Reserva hecha!', 'Booked!') : t('¡Hecho!', 'Done!')),
      'cancelado' => (Icons.cancel, t('No se hizo', 'Not done')),
      'fallido' => (Icons.error, t('No se pudo', 'It didn\'t work')),
      'pasada_a_ti' => (Icons.phone_forwarded, t('Te he pasado la llamada', 'I passed you the call')),
      _ => (Icons.hourglass_empty, t('Preparando…', 'Preparing…')),
    };
    final gradient = switch (order.status) {
      'pedido_hecho' => const LinearGradient(colors: [Color(0xFF065F46), LaiaColors.teal]),
      'cancelado' || 'fallido' => const LinearGradient(colors: [Color(0xFF7F1D1D), LaiaColors.red]),
      'esperando_tu_respuesta' => const LinearGradient(colors: [Color(0xFF9A3412), LaiaColors.orangeDeep]),
      _ => LaiaColors.brandGradient,
    };
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(gradient: gradient, borderRadius: BorderRadius.circular(22)),
      child: Row(
        children: [
          _Pulse(active: !order.isFinished, child: Icon(icon, size: 34, color: Colors.white)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
                const SizedBox(height: 2),
                Text(
                  '${kModeLabels[order.mode] ?? ''}: ${order.items.join(', ')}',
                  style: const TextStyle(color: Colors.white),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (listening)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Row(
                      children: [
                        const Icon(Icons.graphic_eq, color: Colors.white, size: 18),
                        const SizedBox(width: 6),
                        Text(t('Estás escuchando', 'You\'re listening'), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Un aro que late mientras la llamada sigue.
class _Pulse extends StatefulWidget {
  final bool active;
  final Widget child;
  const _Pulse({required this.active, required this.child});

  @override
  State<_Pulse> createState() => _PulseState();
}

class _PulseState extends State<_Pulse> with SingleTickerProviderStateMixin {
  late final _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400));

  @override
  void initState() {
    super.initState();
    if (widget.active) _anim.repeat();
  }

  @override
  void didUpdateWidget(_Pulse old) {
    super.didUpdateWidget(old);
    if (widget.active && !_anim.isAnimating) _anim.repeat();
    if (!widget.active) _anim.stop();
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 60,
      height: 60,
      child: AnimatedBuilder(
        animation: _anim,
        builder: (_, child) => Stack(
          alignment: Alignment.center,
          children: [
            if (widget.active)
              Container(
                width: 40 + 20 * _anim.value,
                height: 40 + 20 * _anim.value,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withValues(alpha: 0.28 * (1 - _anim.value)),
                ),
              ),
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: 0.18)),
            ),
            child!,
          ],
        ),
        child: widget.child,
      ),
    );
  }
}

class _RoundAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final bool active;
  final VoidCallback? onTap;
  const _RoundAction({required this.icon, required this.label, required this.color, this.onTap, this.active = false});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final disabled = onTap == null;
    return Semantics(
      button: true,
      label: label,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: disabled ? color.withValues(alpha: 0.4) : (active ? scheme.surface : color),
                  border: active ? Border.all(color: color, width: 3) : null,
                  boxShadow: [BoxShadow(color: color.withValues(alpha: 0.3), blurRadius: 14, offset: const Offset(0, 5))],
                ),
                child: Icon(icon, color: active ? color : Colors.white, size: 28),
              ),
              const SizedBox(height: 8),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuestionCard extends StatelessWidget {
  final String question;
  final TextEditingController controller;
  final bool sending;
  final void Function(String) onSend;
  const _QuestionCard({required this.question, required this.controller, required this.sending, required this.onSend});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.secondaryContainer,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: scheme.secondary, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(Icons.help, color: scheme.onSecondaryContainer),
              const SizedBox(width: 8),
              Text(t('Laia pregunta', 'Laia asks'), style: TextStyle(fontWeight: FontWeight.w800, color: scheme.onSecondaryContainer)),
            ],
          ),
          const SizedBox(height: 8),
          Text(question, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: scheme.onSecondaryContainer)),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  style: FilledButton.styleFrom(backgroundColor: LaiaColors.teal, foregroundColor: Colors.white),
                  onPressed: sending ? null : () => onSend('Sí'),
                  child: Text(t('Sí', 'Yes')),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  style: FilledButton.styleFrom(backgroundColor: LaiaColors.red, foregroundColor: Colors.white),
                  onPressed: sending ? null : () => onSend('No'),
                  child: const Text('No'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: controller,
            textInputAction: TextInputAction.send,
            onSubmitted: onSend,
            decoration: InputDecoration(
              hintText: t('U otra respuesta: «pide una barbacoa»', 'Or another answer: "order a BBQ one"'),
              suffixIcon: IconButton(
                tooltip: t('Enviar', 'Send'),
                icon: const Icon(Icons.send),
                onPressed: sending ? null : () => onSend(controller.text),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  final Order order;
  const _ResultCard({required this.order});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final r = order.result!;
    final price = r['total_price'];
    final eta = r['eta_minutes'];
    final done = order.status == 'pedido_hecho';
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: done ? scheme.tertiaryContainer : scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            r['summary']?.toString() ?? '',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: done ? scheme.onTertiaryContainer : null),
          ),
          if (price is num && price > 0) ...[
            const SizedBox(height: 8),
            Text('Total: $price ${r['currency'] ?? 'EUR'}',
                style: TextStyle(fontSize: 16, color: done ? scheme.onTertiaryContainer : null)),
          ],
          if (eta is num && eta > 0)
            Text(t('Llega en unos $eta minutos', 'Arrives in about $eta minutes'), style: TextStyle(color: done ? scheme.onTertiaryContainer : null)),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  final TranscriptLine line;
  final bool showOriginal;
  const _Bubble({required this.line, required this.showOriginal});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final laia = line.isLaia;
    final main = showOriginal || line.translation == null ? line.text : line.translation!;
    final secondary = showOriginal ? line.translation : (line.translation == null ? null : line.text);
    final bg = laia ? scheme.primary : scheme.surface;
    final fg = laia ? scheme.onPrimary : scheme.onSurface;
    return Align(
      alignment: laia ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        decoration: BoxDecoration(
          color: bg,
          border: laia ? null : Border.all(color: scheme.outlineVariant),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(laia ? 18 : 4),
            bottomRight: Radius.circular(laia ? 4 : 18),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(laia ? 'Laia' : t('Negocio', 'Business'),
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: fg.withValues(alpha: 0.8))),
            const SizedBox(height: 2),
            Text(main, style: TextStyle(color: fg, fontSize: 15.5)),
            if (secondary != null) ...[
              const SizedBox(height: 4),
              Text(secondary, style: TextStyle(color: fg.withValues(alpha: 0.75), fontSize: 13, fontStyle: FontStyle.italic)),
            ],
          ],
        ),
      ),
    );
  }
}

class _Events extends StatelessWidget {
  final List<String> events;
  const _Events({required this.events});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (events.isEmpty) return const SizedBox.shrink();
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: Text(t('Detalles de la llamada', 'Call details'), style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 14)),
        children: [
          for (final e in events)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 7, right: 10),
                    child: Icon(Icons.circle, size: 7, color: scheme.primary),
                  ),
                  Expanded(child: Text(e)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
