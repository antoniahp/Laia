import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api.dart';
import '../services/storage.dart';
import '../theme.dart';
import '../widgets/language_switch.dart';
import 'shell.dart';
import '../i18n.dart';

/// Entrar o crear cuenta. Para crear cuenta hay que aceptar las condiciones y la privacidad.
class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  final _code = TextEditingController();
  late final _termsTap = TapGestureRecognizer()..onTap = () => _openLegal('terminos');
  late final _privacyTap = TapGestureRecognizer()..onTap = () => _openLegal('privacidad');
  bool _register = true;
  bool _accept = false;
  bool _adult = false;
  bool _busy = false;
  bool _hidePassword = true;
  String? _error;

  @override
  void dispose() {
    for (final c in [_email, _password, _name, _code]) {
      c.dispose();
    }
    _termsTap.dispose();
    _privacyTap.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_register && !(_accept && _adult)) {
      setState(() => _error = t('Para crear la cuenta confirma que eres mayor de edad y acepta las condiciones.', 'To create your account, confirm you are over 18 and accept the terms.'));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final api = await LaiaApi.load();
      final (token, _) = _register
          ? await api.register(_email.text.trim(), _password.text, _name.text.trim(), _code.text.trim(), true)
          : await api.login(_email.text.trim(), _password.text);
      await Storage.setToken(token);
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const Shell()));
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openLegal(String page) async {
    final api = await LaiaApi.load();
    await launchUrl(api.legalPage(page), mode: LaunchMode.inAppBrowserView);
  }

  TextSpan _link(String text, TapGestureRecognizer tap, Color color) {
    return TextSpan(
      text: text,
      recognizer: tap,
      style: TextStyle(color: color, fontWeight: FontWeight.w700, decoration: TextDecoration.underline),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: ListView(
              shrinkWrap: true,
              padding: const EdgeInsets.all(24),
              children: [
                Row(
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: const BoxDecoration(shape: BoxShape.circle, gradient: LaiaColors.micGradient),
                      child: const Icon(Icons.mic_rounded, color: Colors.white, size: 28),
                    ),
                    const SizedBox(width: 14),
                    Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(text: 'Lai', style: TextStyle(color: scheme.onSurface)),
                          TextSpan(text: 'a', style: TextStyle(color: scheme.secondary)),
                        ],
                      ),
                      style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w900, letterSpacing: -1),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const LanguageSwitch(),
                const SizedBox(height: 16),
                Text(t('Dile qué quieres. Ella llama por ti.', 'Tell her what you want. She makes the call.'), style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 16)),
                const SizedBox(height: 28),
                SegmentedButton<bool>(
                  segments: [
                    ButtonSegment(value: true, label: Text(t('Crear cuenta', 'Sign up'))),
                    ButtonSegment(value: false, label: Text(t('Ya tengo cuenta', 'Log in'))),
                  ],
                  selected: {_register},
                  onSelectionChanged: (s) => setState(() {
                    _register = s.first;
                    _error = null;
                  }),
                ),
                const SizedBox(height: 20),
                if (_register) ...[
                  TextField(
                    controller: _name,
                    textCapitalization: TextCapitalization.words,
                    decoration: InputDecoration(labelText: t('Tu nombre', 'Your name'), helperText: t('Solo si el negocio lo pregunta', 'Only if the business asks')),
                  ),
                  const SizedBox(height: 12),
                ],
                TextField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  autofillHints: const [AutofillHints.email],
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  obscureText: _hidePassword,
                  autofillHints: [_register ? AutofillHints.newPassword : AutofillHints.password],
                  decoration: InputDecoration(
                    labelText: t('Contraseña', 'Password'),
                    helperText: _register ? t('Mínimo 8 caracteres', 'At least 8 characters') : null,
                    suffixIcon: IconButton(
                      tooltip: _hidePassword ? t('Mostrar', 'Show') : t('Ocultar', 'Hide'),
                      icon: Icon(_hidePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                      onPressed: () => setState(() => _hidePassword = !_hidePassword),
                    ),
                  ),
                ),
                if (_register) ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: _code,
                    decoration: InputDecoration(
                      labelText: t('Código de invitación', 'Invite code'),
                      helperText: t('Si no tienes uno, déjalo vacío', "Leave it empty if you don't have one"),
                    ),
                  ),
                  const SizedBox(height: 8),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    value: _adult,
                    onChanged: (v) => setState(() => _adult = v ?? false),
                    title: Text(t('Soy mayor de 18 años', 'I am over 18')),
                  ),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    value: _accept,
                    onChanged: (v) => setState(() => _accept = v ?? false),
                    title: Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(text: t('Acepto las ', 'I accept the ')),
                          _link(t('condiciones', 'terms'), _termsTap, scheme.primary),
                          TextSpan(text: t(' y la ', ' and the ')),
                          _link(t('política de privacidad', 'privacy policy'), _privacyTap, scheme.primary),
                        ],
                      ),
                    ),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: TextStyle(color: scheme.error, fontWeight: FontWeight.w600)),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: Text(_busy ? t('Un momento...', 'One moment...') : (_register ? t('Crear cuenta', 'Sign up') : t('Entrar', 'Log in'))),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
