import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api.dart';
import 'common.dart';
import '../i18n.dart';

/// Busca el sitio que has dicho y te deja elegir. Devuelve un negocio listo para llamar.
///
/// Lo de Google Maps solo se enseña; al elegirlo se guarda en tu lista solo su identificador,
/// con el nombre que tú has usado.
Future<Business?> pickPlace(BuildContext context, String search, {String country = ''}) async {
  final api = await LaiaApi.load();
  final List<PlaceCandidate> found;
  try {
    found = await api.searchPlaces(search, country: country);
  } on ApiException catch (e) {
    if (context.mounted) showSnack(context, e.message);
    return null;
  }
  if (!context.mounted) return null;
  final picked = found.length == 1 && !found.first.fromGoogle
      ? found.first
      : await showModalBottomSheet<PlaceCandidate>(
          context: context,
          showDragHandle: true,
          isScrollControlled: true,
          builder: (_) => _PlaceSheet(search: search, places: found),
        );
  if (picked == null) return null;
  final ready = picked.asBusiness;
  if (ready != null) return ready;
  try {
    final label = search.trim().length >= 2 && search.trim().length <= 60 ? search.trim() : picked.name;
    return await api.addPlace(picked.googlePlaceId!, label);
  } on ApiException catch (e) {
    if (context.mounted) showSnack(context, e.message);
    return null;
  }
}

class _PlaceSheet extends StatelessWidget {
  final String search;
  final List<PlaceCandidate> places;
  const _PlaceSheet({required this.search, required this.places});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final anyGoogle = places.any((p) => p.fromGoogle);
    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.75),
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          children: [
            Text(t('¿Cuál es «$search»?', 'Which one is "$search"?'), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(t('Toca el sitio al que quieres que llame Laia.', 'Tap the place you want Laia to call.'), style: TextStyle(color: scheme.onSurfaceVariant)),
            const SizedBox(height: 12),
            for (final p in places)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Material(
                  color: scheme.surface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: scheme.outlineVariant),
                  ),
                  child: ListTile(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    leading: Text(flagOf(p.country), style: const TextStyle(fontSize: 28)),
                    title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                    subtitle: Text(
                      [p.address, if (p.language != 'es') t('Laia hablará en ', 'Laia will speak ') + (Lang.en ? (kLanguages[p.language] ?? p.language) : (kLanguages[p.language]?.toLowerCase() ?? p.language))]
                          .where((s) => s.isNotEmpty)
                          .join('\n'),
                    ),
                    trailing: p.businessId != null
                        ? Icon(Icons.bookmark, color: scheme.primary, semanticLabel: t('En tu lista', 'In your list'))
                        : Icon(Icons.chevron_right, color: scheme.onSurfaceVariant),
                    onTap: () => Navigator.pop(context, p),
                  ),
                ),
              ),
            if (anyGoogle)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Align(alignment: Alignment.centerRight, child: GoogleMapsAttribution()),
              ),
          ],
        ),
      ),
    );
  }
}
