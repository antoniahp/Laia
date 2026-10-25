import 'dart:async';

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../widgets/common.dart';
import '../widgets/place_picker.dart';
import '../i18n.dart';

/// Tus sitios: los que ya has usado, buscar uno nuevo en Google Maps o proponerlo a mano.
/// En [pickMode], tocar un negocio verificado lo devuelve a la pantalla anterior.
class BusinessesScreen extends StatefulWidget {
  final bool pickMode;
  const BusinessesScreen({super.key, this.pickMode = false});

  @override
  State<BusinessesScreen> createState() => _BusinessesScreenState();
}

class _BusinessesScreenState extends State<BusinessesScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  List<Business> _list = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await (await LaiaApi.load()).businesses(_search.text.trim());
      if (mounted) setState(() => _list = list);
    } on ApiException catch (e) {
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// Busca en Google Maps lo que has escrito y lo añade a tu lista al elegirlo.
  Future<void> _discover() async {
    final query = _search.text.trim();
    if (query.length < 2) {
      _snack(t('Escribe el nombre del sitio y la ciudad.', 'Type the place name and the city.'));
      return;
    }
    FocusScope.of(context).unfocus();
    final business = await pickPlace(context, query);
    if (business == null || !mounted) return;
    if (widget.pickMode) {
      Navigator.pop(context, business);
      return;
    }
    _snack(t('${business.name} está en tu lista.', '${business.name} is in your list.'));
    await _load();
  }

  void _onSearch(String _) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), _load);
  }

  Future<void> _propose() async {
    final created = await showDialog<Business>(context: context, builder: (_) => const _ProposeDialog());
    if (created == null) return;
    _snack(created.isVerified
        ? t('${created.name} está verificado. ¡Ya puedes pedir!', '${created.name} is verified. You can order now!')
        : t('Gracias. Revisaremos ${created.name} y te avisaremos.', 'Thanks. We\'ll review ${created.name} and let you know.'));
    await _load();
  }

  void _snack(String msg) {
    if (mounted) showSnack(context, msg);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(widget.pickMode ? t('Elige un sitio', 'Choose a place') : t('Mis sitios', 'My places'))),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _propose,
        icon: const Icon(Icons.add_business_outlined),
        label: Text(t('Proponer', 'Suggest')),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              controller: _search,
              onChanged: _onSearch,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _discover(),
              decoration: InputDecoration(prefixIcon: Icon(Icons.search), hintText: t('Nombre y ciudad: Tres Hermanas Madrid', 'Name and city: Tres Hermanas Madrid')),
            ),
          ),
          Align(
            alignment: Alignment.centerLeft,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: TextButton.icon(
                onPressed: _loading ? null : _discover,
                icon: const Icon(Icons.travel_explore),
                label: Text(t('Buscar un sitio nuevo', 'Search a new place')),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              t('Laia solo llama a negocios verificados. Los de Google Maps lo están al momento; ', 'Laia only calls verified businesses. Google Maps ones are verified instantly; ') +
                  t('si el tuyo no aparece, propónlo a mano y lo revisamos.', 'if yours isn\'t there, suggest it and we\'ll review it.'),
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _list.isEmpty
                    ? Center(child: Text(t('Aún no tienes sitios. Busca uno arriba.', 'No places yet. Search one above.')))
                    : ListView.builder(
                        padding: const EdgeInsets.only(bottom: 96),
                        itemCount: _list.length,
                        itemBuilder: (_, i) {
                          final b = _list[i];
                          return ListTile(
                            leading: Text(b.country.isEmpty ? '📞' : flagOf(b.country), style: const TextStyle(fontSize: 26)),
                            title: Text(b.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                            subtitle: Text([b.address, kLanguages[b.language] ?? b.language, if (b.isFromGoogle) 'Google Maps']
                                .where((s) => s.isNotEmpty)
                                .join(' · ')),
                            trailing: b.isVerified
                                ? Icon(Icons.verified, color: scheme.primary)
                                : Chip(
                                    label: Text(b.status == 'rechazado' ? t('Rechazado', 'Rejected') : t('En revisión', 'Under review')),
                                    visualDensity: VisualDensity.compact,
                                  ),
                            onTap: widget.pickMode && b.isVerified ? () => Navigator.pop(context, b) : null,
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

class _ProposeDialog extends StatefulWidget {
  const _ProposeDialog();

  @override
  State<_ProposeDialog> createState() => _ProposeDialogState();
}

class _ProposeDialogState extends State<_ProposeDialog> {
  final _name = TextEditingController();
  final _phone = TextEditingController(text: '+34 ');
  final _city = TextEditingController();
  String _lang = 'es';
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _city.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final b = await (await LaiaApi.load()).proposeBusiness(_name.text.trim(), _phone.text.trim(), _lang, _city.text.trim());
      if (mounted) Navigator.pop(context, b);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(t('Proponer negocio', 'Suggest a business')),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: _name, decoration: InputDecoration(labelText: t('Nombre del negocio', 'Business name'))),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(labelText: t('Teléfono', 'Phone'), helperText: t('Con prefijo del país', 'With country code')),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _city,
              decoration: InputDecoration(labelText: t('Ciudad', 'City'), helperText: t('Ayuda a verificarlo', 'Helps us verify it')),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _lang,
              decoration: InputDecoration(labelText: t('Idioma del negocio', 'Business language')),
              items: [
                for (final e in kLanguages.entries)
                  DropdownMenuItem(value: e.key, child: Text('${kFlags[e.key]} ${e.value}')),
              ],
              onChanged: (v) => setState(() => _lang = v ?? 'es'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: _busy ? null : () => Navigator.pop(context), child: Text(t('Cancelar', 'Cancel'))),
        FilledButton(onPressed: _busy ? null : _save, child: Text(_busy ? t('Enviando...', 'Sending...') : t('Enviar', 'Send'))),
      ],
    );
  }
}
