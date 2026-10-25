import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/cta_button.dart';
import 'call_screen.dart';
import '../i18n.dart';

/// «Laia va a llamar para esto»: revisas y confirmas. Devuelve true si se ha llamado.
class ReviewScreen extends StatefulWidget {
  final AppUser user;
  final OrderDraft draft;
  const ReviewScreen({super.key, required this.user, required this.draft});

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late final TextEditingController _items;
  late final TextEditingController _alts;
  late final TextEditingController _price;
  late final TextEditingController _notes;
  bool _calling = false;

  OrderDraft get d => widget.draft;

  @override
  void initState() {
    super.initState();
    _items = TextEditingController(text: d.items.join(', '));
    _alts = TextEditingController(text: d.alternatives.join(', '));
    _price = TextEditingController(text: d.maxPrice == null ? '' : _fmt(d.maxPrice!));
    _notes = TextEditingController(text: d.notes);
    if (!kModeLabels.containsKey(d.mode)) d.mode = 'pedido';
  }

  @override
  void dispose() {
    for (final c in [_items, _alts, _price, _notes]) {
      c.dispose();
    }
    super.dispose();
  }

  String _fmt(double v) => v == v.roundToDouble() ? v.toStringAsFixed(0) : v.toStringAsFixed(2);

  List<String> _split(String s) => s.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();

  Future<void> _call() async {
    d.items = _split(_items.text);
    d.alternatives = d.mode == 'pedido' ? _split(_alts.text) : [];
    d.maxPrice = d.mode == 'pedido' ? double.tryParse(_price.text.replaceAll(',', '.').trim()) : null;
    d.notes = _notes.text.trim();
    if (d.items.isEmpty) {
      showSnack(context, d.mode == 'pedido' ? t('¿Qué pido? Escribe al menos un producto.', 'What should I order? Write at least one item.') : t('Escribe qué tiene que hacer Laia.', 'Write what Laia has to do.'));
      return;
    }
    setState(() => _calling = true);
    try {
      final order = await (await LaiaApi.load()).createOrder(d);
      if (!mounted) return;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => CallScreen(orderId: order.id)));
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) {
        showSnack(context, e.message);
        setState(() => _calling = false);
      }
    }
  }

  String get _whatLabel => switch (d.mode) {
        'reserva' => t('Qué reservar (personas, día y hora)', 'What to book (people, day and time)'),
        'consulta' => t('Qué preguntar', 'What to ask'),
        _ => t('Qué pedir', 'What to order'),
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final b = d.business;
    final lang = Lang.en ? (kLanguages[b.language] ?? b.language) : (kLanguages[b.language] ?? b.language).toLowerCase();
    final who = widget.user.firstName.isEmpty ? t('tu nombre', 'your name') : widget.user.firstName;
    return Scaffold(
      appBar: AppBar(title: Text(t('Revisa antes de llamar', 'Check before calling'))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: b.isAbroad ? LaiaColors.abroadGradient : LaiaColors.brandGradient,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: [
                  Text(b.country.isEmpty ? '📞' : flagOf(b.country), style: const TextStyle(fontSize: 36)),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(t('Laia llamará a', 'Laia will call'),
                            style: TextStyle(color: Colors.white.withValues(alpha: 0.85), fontSize: 13)),
                        Text(b.name,
                            style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800)),
                        Text(t('Hablará en $lang${b.language == 'es' ? '' : ' y te lo traducirá'}', 'She will speak $lang'),
                            style: const TextStyle(color: Colors.white)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            SegmentedButton<String>(
              segments: [
                ButtonSegment(value: 'pedido', label: Text(t('Pedir', 'Order')), icon: const Icon(Icons.shopping_bag_outlined)),
                ButtonSegment(value: 'reserva', label: Text(t('Reservar', 'Book')), icon: const Icon(Icons.event_available_outlined)),
                ButtonSegment(value: 'consulta', label: Text(t('Preguntar', 'Ask')), icon: const Icon(Icons.help_outline)),
              ],
              selected: {d.mode},
              showSelectedIcon: false,
              onSelectionChanged: (s) => setState(() => d.mode = s.first),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _items,
              minLines: 1,
              maxLines: 3,
              decoration: InputDecoration(labelText: _whatLabel, helperText: d.mode == 'pedido' ? t('Separa con comas', 'Separate with commas') : null),
            ),
            if (d.mode == 'pedido') ...[
              const SizedBox(height: 12),
              TextField(
                controller: _alts,
                decoration: InputDecoration(labelText: t('Si no hay, pide…', 'If they\'re out, order…'), helperText: t('Opcional, en orden', 'Optional, in order')),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _price,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: t('Precio máximo', 'Max price'),
                  suffixText: '€',
                  helperText: t('Vacío = sin límite. Si cuesta más, Laia no lo acepta.', 'Empty = no limit. If it costs more, Laia won\'t accept it.'),
                ),
              ),
            ],
            const SizedBox(height: 12),
            TextField(
              controller: _notes,
              decoration: InputDecoration(
                labelText: t('Notas', 'Notes'),
                hintText: d.mode == 'reserva' ? t('Terraza si puede ser, una trona…', 'Terrace if possible, a high chair…') : t('Sin cebolla, bien hecha…', 'No onion, well done…'),
              ),
            ),
            if (d.mode == 'pedido')
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(t('Pregúntame antes de cambiar', 'Ask me before switching')),
                subtitle: Text(t('Si no hay lo que quieres, Laia te pregunta aquí y por Telegram', 'If they don\'t have it, Laia asks you here and on Telegram')),
                value: d.askBeforeAlternative,
                onChanged: (v) => setState(() => d.askBeforeAlternative = v),
              ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (d.mode == 'pedido')
                    _Fact(
                      Icons.home_outlined,
                      widget.user.address.isEmpty
                          ? t('Sin dirección de entrega: añádela en Perfil', 'No delivery address: add it in Profile')
                          : t('Entrega en ${widget.user.address}', 'Delivery to ${widget.user.address}'),
                      warn: widget.user.address.isEmpty,
                    ),
                  if (d.mode == 'reserva')
                    _Fact(Icons.badge_outlined, t('A nombre de $who', 'Under the name $who') + (widget.user.phone.isEmpty ? '' : t(', teléfono ', ', phone ') + widget.user.phone)),
                  _Fact(Icons.smart_toy_outlined, t('Se presentará como IA y podrás escuchar la llamada en directo', 'She\'ll introduce herself as an AI and you can listen live')),
                  _Fact(Icons.credit_card_off_outlined, t('Nunca da datos de tarjeta: pagas tú al negocio', 'She never gives card details: you pay the business')),
                ],
              ),
            ),
            const SizedBox(height: 20),
            CtaButton(label: _calling ? t('Llamando…', 'Calling…') : t('Llamar ahora', 'Call now'), icon: Icons.call, busy: _calling, onPressed: _call),
          ],
        ),
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  final IconData icon;
  final String text;
  final bool warn;
  const _Fact(this.icon, this.text, {this.warn = false});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final color = warn ? scheme.error : scheme.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: TextStyle(color: warn ? scheme.error : scheme.onSurface))),
        ],
      ),
    );
  }
}
