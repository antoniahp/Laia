import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/models.dart';
import '../services/speaker.dart';
import '../theme.dart';
import 'voice.dart';
import '../i18n.dart';

/// Manos libres: «Llamo a X para pedir Y». Llama sola a los pocos segundos salvo que digas «no».
Future<bool> confirmHandsFree(BuildContext context, OrderDraft draft, {int seconds = 5}) async {
  final ok = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (_) => _Countdown(draft: draft, seconds: seconds),
  );
  return ok ?? false;
}

class _Countdown extends StatefulWidget {
  final OrderDraft draft;
  final int seconds;
  const _Countdown({required this.draft, required this.seconds});

  @override
  State<_Countdown> createState() => _CountdownState();
}

class _CountdownState extends State<_Countdown> {
  final _voice = VoiceInput();
  late int _left = widget.seconds;
  Timer? _timer;
  bool _closed = false;

  static final _stop = RegExp(r'\b(no|cancela|cancelar|para|espera|stop|quieto|cancel|wait|nope)\b', caseSensitive: false);
  static final _go = RegExp(r'\b(s[ií]|vale|llama|venga|dale|ok|okay|yes|yeah|yep|call|go)\b', caseSensitive: false);

  @override
  void initState() {
    super.initState();
    HapticFeedback.heavyImpact();
    _start();
  }

  /// Primero Laia pregunta en voz alta; después escucha y cuenta hasta llamar.
  Future<void> _start() async {
    final d = widget.draft;
    final what = switch (d.mode) {
      'reserva' => t('reservar', 'book'),
      'consulta' => t('preguntar', 'ask about'),
      _ => t('pedir', 'order'),
    };
    await Speaker.say(t('¿Listo? Llamo a ${d.business.name} para $what ${d.items.join(' y ')}.', 'Ready? Calling ${d.business.name} to $what ${d.items.join(' and ')}.'));
    if (_closed || !mounted) return;
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_left <= 1) {
        _close(true);
      } else {
        setState(() => _left--);
      }
    });
    _listen();
  }

  Future<void> _listen() async {
    if (_closed) return;
    await _voice.listenOnce(
      onChange: () {},
      onStopped: () => Future.delayed(const Duration(milliseconds: 200), _listen),
      onResult: (text, _) {
        if (_stop.hasMatch(text)) {
          _close(false);
        } else if (_go.hasMatch(text)) {
          _close(true);
        }
      },
    );
  }

  void _close(bool call) {
    if (_closed) return;
    _closed = true;
    Speaker.stop();
    _timer?.cancel();
    _voice.stop();
    if (mounted) Navigator.pop(context, call);
  }

  @override
  void dispose() {
    _closed = true;
    _timer?.cancel();
    _voice.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final d = widget.draft;
    final what = switch (d.mode) {
      'reserva' => t('reservar', 'book'),
      'consulta' => t('preguntar', 'ask about'),
      _ => t('pedir', 'order'),
    };
    final rules = [
      if (d.alternatives.isNotEmpty) t('si no hay: ', 'if not: ') + d.alternatives.join(', '),
      if (d.maxPrice != null) t('máximo ', 'max ') + '${d.maxPrice!.toStringAsFixed(d.maxPrice! % 1 == 0 ? 0 : 2)} €',
    ];
    return Dialog(
      insetPadding: const EdgeInsets.all(20),
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(gradient: LaiaColors.brandGradient, borderRadius: BorderRadius.circular(28)),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              t('Llamo a ${d.business.name}', 'Calling ${d.business.name}'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
            ),
            const SizedBox(height: 8),
            Text(
              '${t('para', 'to')} $what: ${d.items.join(', ')}${rules.isEmpty ? '' : '\n(${rules.join(' · ')})'}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFE6E8FF), fontSize: 17, height: 1.35),
            ),
            const SizedBox(height: 22),
            Container(
              width: 96,
              height: 96,
              decoration: const BoxDecoration(shape: BoxShape.circle, gradient: LaiaColors.micGradient),
              alignment: Alignment.center,
              child: Text('$_left', style: const TextStyle(color: Colors.white, fontSize: 44, fontWeight: FontWeight.w900)),
            ),
            const SizedBox(height: 16),
            Text(
              t('Di «sí» para llamar ya o «no» para cancelar', 'Say "yes" to call now or "no" to cancel'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white70),
                    ),
                    onPressed: () => _close(false),
                    child: Text(t('Cancelar', 'Cancel')),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(50),
                      backgroundColor: Colors.white,
                      foregroundColor: LaiaColors.indigoDeep,
                    ),
                    onPressed: () => _close(true),
                    child: Text(t('Llamar ya', 'Call now')),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
