import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/cta_button.dart';
import '../widgets/place_picker.dart';
import '../widgets/voice.dart';
import 'review_screen.dart';
import '../i18n.dart';

/// «Extranjero»: llamar a un sitio de otro país. Tú hablas en español; Laia, en su idioma.
class AbroadTab extends StatefulWidget {
  const AbroadTab({super.key});

  @override
  State<AbroadTab> createState() => _AbroadTabState();
}

class _AbroadTabState extends State<AbroadTab> {
  final _voice = VoiceInput();
  final _place = TextEditingController();
  final _command = TextEditingController();

  List<Country> _countries = [];
  Country? _country;
  Business? _business;
  String? _error;
  bool _searching = false;
  bool _busy = false;

  static List<(String, String)> get _ideas => [
    ('🍝', t('Reserva mesa para 2 el viernes a las 20:30', 'Book a table for 2 on Friday at 8:30 pm')),
    ('🏨', t('Pregunta si tienen habitación libre del 3 al 5 de mayo y el precio', 'Ask if they have a room from May 3 to 5 and the price')),
    ('🚗', t('Pregunta si el parking del hotel es gratis', 'Ask if the hotel parking is free')),
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _voice.dispose();
    _place.dispose();
    _command.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final list = await (await LaiaApi.load()).countries();
      if (!mounted) return;
      final abroad = list.where((c) => c.code != 'ES').toList();
      setState(() {
        _countries = abroad;
        _country ??= abroad.isEmpty ? null : abroad.first;
        _error = null;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _search() async {
    final text = _place.text.trim();
    if (_country == null) return;
    if (text.length < 2) {
      showSnack(context, t('Escribe el nombre del sitio (y la ciudad si puedes).', 'Type the place name (and the city if you can).'));
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() => _searching = true);
    final business = await pickPlace(context, text, country: _country!.code);
    if (!mounted) return;
    setState(() {
      _searching = false;
      if (business != null) _business = business;
    });
  }

  Future<void> _mic() async {
    final error = await _voice.toggle(
      onText: (text) => setState(() => _command.text = text),
      onChange: () {
        if (mounted) setState(() {});
      },
    );
    if (error != null && mounted) showSnack(context, error);
  }

  Future<void> _prepare() async {
    final business = _business;
    final command = _command.text.trim();
    if (business == null) {
      showSnack(context, t('Primero busca y elige el sitio.', 'First search and choose the place.'));
      return;
    }
    if (command.isEmpty) {
      showSnack(context, t('Dime qué quieres que pida o pregunte.', 'Tell me what to order or ask.'));
      return;
    }
    setState(() => _busy = true);
    try {
      final api = await LaiaApi.load();
      final parsed = await api.parse(command, business);
      final user = await api.me();
      if (!mounted) return;
      final placed = await Navigator.push<bool>(
        context,
        MaterialPageRoute(builder: (_) => ReviewScreen(user: user, draft: parsed.toDraft(business))),
      );
      if (placed == true && mounted) setState(() => _command.clear());
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final country = _country;
    final business = _business;
    final language = business != null
        ? (Lang.en ? (kLanguages[business.language] ?? business.language) : (kLanguages[business.language] ?? business.language).toLowerCase())
        : country?.languageName ?? '';
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      children: [
        GradientHeader(
          title: t('Llama al extranjero 🌍', 'Call abroad 🌍'),
          subtitle: t('Tú hablas en español. Laia llama en su idioma y te traduce toda la conversación.', 'You write in your language. Laia calls in theirs and translates the conversation for you.'),
          gradient: LaiaColors.abroadGradient,
        ),
        const SizedBox(height: 20),
        if (_error != null)
          Card(
            child: ListTile(
              leading: Icon(Icons.wifi_off, color: scheme.error),
              title: Text(_error!),
              trailing: TextButton(onPressed: _load, child: Text(t('Reintentar', 'Retry'))),
            ),
          ),
        SectionTitle(t('1. ¿En qué país?', '1. Which country?')),
        SizedBox(
          height: 96,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _countries.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              final c = _countries[i];
              final on = c.code == country?.code;
              return _CountryTile(
                country: c,
                selected: on,
                onTap: () => setState(() {
                  _country = c;
                  if (_business != null && _business!.country != c.code) _business = null;
                }),
              );
            },
          ),
        ),
        const SizedBox(height: 22),
        SectionTitle(t('2. ¿A qué sitio llamo${country == null ? '' : ' en ${country.name}'}?', '2. Which place should I call${country == null ? '' : ' in ${country.name}'}?')),
        TextField(
          controller: _place,
          textInputAction: TextInputAction.search,
          onSubmitted: (_) => _search(),
          decoration: InputDecoration(
            hintText: t('Trattoria da Enzo, Roma', 'Trattoria da Enzo, Rome'),
            prefixIcon: const Icon(Icons.search),
            suffixIcon: _searching
                ? const Padding(padding: EdgeInsets.all(14), child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)))
                : IconButton(tooltip: t('Buscar', 'Search'), icon: const Icon(Icons.arrow_forward), onPressed: _search),
          ),
        ),
        if (business != null) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: scheme.tertiaryContainer,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                Text(flagOf(business.country), style: const TextStyle(fontSize: 30)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(business.name,
                          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: scheme.onTertiaryContainer)),
                      Text(t('Laia hablará en $language', 'Laia will speak $language'), style: TextStyle(color: scheme.onTertiaryContainer)),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: t('Cambiar de sitio', 'Change place'),
                  icon: Icon(Icons.close, color: scheme.onTertiaryContainer),
                  onPressed: () => setState(() => _business = null),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 22),
        SectionTitle(t('3. ¿Qué quieres? Dímelo en español', '3. What do you want? Tell me')),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: TextField(
                controller: _command,
                minLines: 2,
                maxLines: 4,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(hintText: t('Reserva mesa para 2 el viernes a las 20:30', 'Book a table for 2 on Friday at 8:30 pm')),
              ),
            ),
            const SizedBox(width: 12),
            MicButton(listening: _voice.listening, onTap: _mic, size: 64, gradient: LaiaColors.abroadGradient),
          ],
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final (emoji, text) in _ideas)
              ActionChip(label: Text('$emoji $text'), onPressed: () => setState(() => _command.text = text)),
          ],
        ),
        const SizedBox(height: 24),
        CtaButton(
          label: _busy ? t('Laia está pensando…', 'Laia is thinking…') : t('Preparar llamada', 'Prepare call'),
          icon: Icons.translate,
          busy: _busy,
          onPressed: _prepare,
        ),
        const SizedBox(height: 14),
        Text(
          t('Laia llama desde su propio número: tú no pagas llamada internacional ni roaming. ', 'Laia calls from her own number: you don\'t pay for international calls or roaming. ') +
              t('Verás cada frase en el idioma original y traducida al español.', 'You\'ll see every line in the original language and translated.'),
          style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
        ),
      ],
    );
  }
}

class _CountryTile extends StatelessWidget {
  final Country country;
  final bool selected;
  final VoidCallback onTap;
  const _CountryTile({required this.country, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      selected: selected,
      button: true,
      label: '${country.name}, ${country.languageName}',
      child: Material(
        color: selected ? LaiaColors.teal : scheme.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: selected ? LaiaColors.teal : scheme.outlineVariant, width: 1.5),
        ),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: SizedBox(
            width: 104,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(country.flag, style: const TextStyle(fontSize: 30)),
                const SizedBox(height: 4),
                Text(
                  country.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontWeight: FontWeight.w700, color: selected ? Colors.white : scheme.onSurface),
                ),
                Text(
                  country.languageName,
                  style: TextStyle(fontSize: 12, color: selected ? const Color(0xFFD1FAE5) : scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
