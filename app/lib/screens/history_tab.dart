import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../theme.dart';
import 'call_screen.dart';
import '../i18n.dart';

/// «Llamadas»: todo lo que ha hecho Laia por ti.
class HistoryTab extends StatefulWidget {
  const HistoryTab({super.key});

  @override
  State<HistoryTab> createState() => _HistoryTabState();
}

class _HistoryTabState extends State<HistoryTab> {
  List<Order>? _orders;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final list = await (await LaiaApi.load()).orders();
      if (mounted) {
        setState(() {
          _orders = list;
          _error = null;
        });
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  String _date(DateTime? d) {
    if (d == null) return '';
    final l = d.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(l.day)}/${two(l.month)} · ${two(l.hour)}:${two(l.minute)}';
  }

  (Color, IconData) _look(Order o) => switch (o.status) {
        'pedido_hecho' => (LaiaColors.teal, Icons.check_circle),
        'cancelado' || 'fallido' => (LaiaColors.red, Icons.cancel),
        'pasada_a_ti' => (LaiaColors.indigo, Icons.phone_forwarded),
        'esperando_tu_respuesta' => (LaiaColors.orangeDeep, Icons.notifications_active),
        _ => (LaiaColors.indigo, Icons.phone_in_talk),
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final orders = _orders;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          Text(t('Tus llamadas', 'Your calls'), style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(t('Las conversaciones se borran a los 30 días; el resultado se queda.', 'Conversations are deleted after 30 days; the result stays.'),
              style: TextStyle(color: scheme.onSurfaceVariant)),
          const SizedBox(height: 16),
          if (_error != null)
            Text(_error!, style: TextStyle(color: scheme.error))
          else if (orders == null)
            const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()))
          else if (orders.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 48),
              child: Column(
                children: [
                  Icon(Icons.phone_disabled_outlined, size: 56, color: scheme.onSurfaceVariant),
                  const SizedBox(height: 12),
                  Text(t('Aún no has pedido nada', 'Nothing ordered yet'), style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  Text(t('Ve a «Pedir» y dile a Laia qué quieres.', 'Go to "Ask" and tell Laia what you want.'), style: TextStyle(color: scheme.onSurfaceVariant)),
                ],
              ),
            )
          else
            for (final o in orders)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    leading: CircleAvatar(
                      backgroundColor: _look(o).$1,
                      foregroundColor: Colors.white,
                      child: Icon(_look(o).$2),
                    ),
                    title: Text(
                      '${o.isForeign ? '${kFlags[o.language] ?? ''} ' : ''}${o.businessName}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    subtitle: Text(
                      '${(o.result?['summary'] as String?) ?? o.items.join(', ')}\n${_date(o.createdAt)}',
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                    isThreeLine: true,
                    trailing: Text(
                      kStatusLabels[o.status] ?? o.status,
                      style: TextStyle(color: _look(o).$1, fontWeight: FontWeight.w700),
                    ),
                    onTap: () async {
                      await Navigator.push(context, MaterialPageRoute(builder: (_) => CallScreen(orderId: o.id)));
                      _load();
                    },
                  ),
                ),
              ),
        ],
      ),
    );
  }
}
