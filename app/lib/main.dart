import 'package:flutter/material.dart';

import 'i18n.dart';
import 'screens/auth_screen.dart';
import 'screens/intro_screen.dart';
import 'screens/shell.dart';
import 'services/storage.dart';
import 'theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Lang.load();
  runApp(const LaiaApp());
}

class LaiaApp extends StatelessWidget {
  const LaiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Al cambiar de idioma se redibuja toda la app
    return ValueListenableBuilder<String>(
      valueListenable: Lang.current,
      builder: (context, lang, _) => MaterialApp(
        key: ValueKey(lang),
        title: 'Laia',
        debugShowCheckedModeBanner: false,
        theme: laiaTheme(Brightness.light),
        darkTheme: laiaTheme(Brightness.dark),
        home: const StartGate(),
      ),
    );
  }
}

/// Al abrir: la presentación la primera vez, luego entrar, y si ya tienes sesión, directo a Laia.
class StartGate extends StatelessWidget {
  const StartGate({super.key});

  Future<Widget> _first() async {
    if (!await Storage.introSeen()) return const IntroScreen();
    return await Storage.token() == null ? const AuthScreen() : const Shell();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Widget>(
      future: _first(),
      builder: (context, snap) => snap.data ?? const Scaffold(body: Center(child: CircularProgressIndicator())),
    );
  }
}
