import 'package:flutter/material.dart';

import '../services/storage.dart';
import '../theme.dart';
import 'auth_screen.dart';
import '../i18n.dart';
import '../widgets/language_switch.dart';

/// La primera vez: qué hace Laia, en tres pantallas.
class IntroScreen extends StatefulWidget {
  const IntroScreen({super.key});

  @override
  State<IntroScreen> createState() => _IntroScreenState();
}

class _IntroScreenState extends State<IntroScreen> {
  final _pages = PageController();
  int _page = 0;

  List<(IconData, String, String)> get _slides => [
    (
      Icons.mic_rounded,
      t('Dile qué quieres', 'Tell her what you want'),
      t('«Pide una cuatro quesos en Tres Hermanas. Si no hay, una margarita. Máximo 20 euros.»',
          '"Order a four-cheese pizza from Tres Hermanas. If they\'re out, a margherita. Max 20 euros."'),
    ),
    (
      Icons.support_agent_rounded,
      t('Laia llama por ti', 'Laia calls for you'),
      t('Busca el sitio, llama y sigue tus reglas. Siempre se presenta como IA.',
          'She finds the place, calls and follows your rules. She always says she is an AI.'),
    ),
    (
      Icons.headphones_rounded,
      t('Escucha o habla tú', 'Listen or take over'),
      t('Oye la llamada en directo, responde sus dudas con un toque o pide que te la pase.',
          'Listen live, answer her questions with one tap or ask her to pass you the call.'),
    ),
    (
      Icons.translate_rounded,
      t('También en otros idiomas', 'In other languages too'),
      t('Llama a un restaurante en Roma o a un hotel en Berlín. Laia habla su idioma y te lo traduce.',
          'Call a restaurant in Rome or a hotel in Berlin. Laia speaks their language and translates for you.'),
    ),
  ];

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  Future<void> _done() async {
    await Storage.setIntroSeen();
    if (!mounted) return;
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
  }

  @override
  Widget build(BuildContext context) {
    final last = _page == _slides.length - 1;
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: LaiaColors.brandGradient),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 4, 0),
                child: Row(
                  children: [
                    const Expanded(child: Align(alignment: Alignment.centerLeft, child: LanguageSwitch())),
                    TextButton(
                      onPressed: _done,
                      style: TextButton.styleFrom(foregroundColor: Colors.white),
                      child: Text(t('Saltar', 'Skip')),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _pages,
                  itemCount: _slides.length,
                  onPageChanged: (i) => setState(() => _page = i),
                  itemBuilder: (_, i) {
                    final (icon, title, text) = _slides[i];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 132,
                            height: 132,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LaiaColors.micGradient,
                              boxShadow: [
                                BoxShadow(color: Colors.black.withValues(alpha: 0.25), blurRadius: 30, offset: const Offset(0, 12)),
                              ],
                            ),
                            child: Icon(icon, size: 64, color: Colors.white),
                          ),
                          const SizedBox(height: 36),
                          Text(
                            title,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.white, fontSize: 30, fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 14),
                          Text(
                            text,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Color(0xFFE6E8FF), fontSize: 17, height: 1.45),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < _slides.length; i++)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.all(4),
                      width: i == _page ? 24 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: i == _page ? Colors.white : Colors.white38,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                ],
              ),
              Padding(
                padding: const EdgeInsets.all(24),
                child: FilledButton(
                  style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: LaiaColors.indigoDeep),
                  onPressed: last
                      ? _done
                      : () => _pages.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeOut),
                  child: Text(last ? t('Empezar', 'Start') : t('Siguiente', 'Next')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
