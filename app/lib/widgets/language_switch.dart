import 'package:flutter/material.dart';

import '../i18n.dart';

/// Selector Español / English.
class LanguageSwitch extends StatelessWidget {
  const LanguageSwitch({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: Lang.current,
      builder: (context, lang, _) => SegmentedButton<String>(
        showSelectedIcon: false,
        segments: const [
          ButtonSegment(value: 'es', label: Text('🇪🇸 Español')),
          ButtonSegment(value: 'en', label: Text('🇬🇧 English')),
        ],
        selected: {lang},
        onSelectionChanged: (s) => Lang.set(s.first),
      ),
    );
  }
}
