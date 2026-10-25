import 'package:flutter/material.dart';

import 'abroad_tab.dart';
import 'ask_tab.dart';
import 'history_tab.dart';
import 'profile_tab.dart';
import '../i18n.dart';

/// Las cuatro pestañas de Laia.
class Shell extends StatefulWidget {
  const Shell({super.key});

  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int _tab = 0;
  int _version = 0; // al cambiar de pestaña, se recarga lo que se ve

  void _select(int i) => setState(() {
        _tab = i;
        _version++;
      });

  @override
  Widget build(BuildContext context) {
    final tabs = [
      AskTab(key: ValueKey('ask$_version'), active: _tab == 0),
      AbroadTab(key: const ValueKey('abroad')),
      HistoryTab(key: ValueKey('history$_version')),
      ProfileTab(key: ValueKey('profile$_version')),
    ];
    return Scaffold(
      body: SafeArea(bottom: false, child: IndexedStack(index: _tab, children: tabs)),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: _select,
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.mic_none_rounded),
            selectedIcon: const Icon(Icons.mic_rounded),
            label: t('Pedir', 'Ask'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.public_outlined),
            selectedIcon: const Icon(Icons.public),
            label: t('Extranjero', 'Abroad'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.receipt_long_outlined),
            selectedIcon: const Icon(Icons.receipt_long),
            label: t('Llamadas', 'Calls'),
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline),
            selectedIcon: const Icon(Icons.person),
            label: t('Perfil', 'Profile'),
          ),
        ],
      ),
    );
  }
}
