import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/models.dart';
import '../services/api.dart';
import '../services/storage.dart';
import '../widgets/common.dart';
import 'auth_screen.dart';
import 'businesses_screen.dart';
import '../i18n.dart';
import '../widgets/language_switch.dart';

/// Perfil como pantalla aparte (desde los avisos de «Pedir»).
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: Text(t('Perfil', 'Profile'))), body: const ProfileTab());
}

/// «Perfil»: tus datos, Telegram, tus sitios, privacidad y legal.
class ProfileTab extends StatefulWidget {
  const ProfileTab({super.key});

  @override
  State<ProfileTab> createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  final _name = TextEditingController();
  final _address = TextEditingController();
  final _phone = TextEditingController();
  final _server = TextEditingController();
  AppUser? _user;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [_name, _address, _phone, _server]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    _server.text = await Storage.serverUrl();
    try {
      final user = await (await LaiaApi.load()).me();
      if (!mounted) return;
      setState(() {
        _user = user;
        _name.text = user.name;
        _address.text = user.address;
        _phone.text = user.phone;
      });
    } on ApiException catch (e) {
      if (e.status == 401) return _logout();
      if (mounted) showSnack(context, e.message);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await Storage.setServerUrl(_server.text);
      final user = await (await LaiaApi.load()).updateMe(
        name: _name.text.trim(),
        address: _address.text.trim(),
        phone: _phone.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _user = user;
        _phone.text = user.phone;
      });
      showSnack(context, t('Guardado ✓', 'Saved ✓'));
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _connectTelegram() async {
    try {
      final url = await (await LaiaApi.load()).telegramLink();
      final ok = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      if (!mounted) return;
      if (!ok) {
        await Clipboard.setData(ClipboardData(text: url));
        if (mounted) showSnack(context, t('Enlace copiado. Ábrelo en Telegram.', 'Link copied. Open it in Telegram.'));
      } else {
        showSnack(context, t('Pulsa «Iniciar» en Telegram y vuelve aquí.', 'Tap "Start" in Telegram and come back.'));
      }
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    }
  }

  Future<void> _openLegal(String page) async {
    final api = await LaiaApi.load();
    await launchUrl(api.legalPage(page), mode: LaunchMode.inAppBrowserView);
  }

  Future<void> _export() async {
    try {
      final json = await (await LaiaApi.load()).exportMyData();
      await Clipboard.setData(ClipboardData(text: json));
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(t('Tus datos', 'Your data')),
          content: SizedBox(
            width: double.maxFinite,
            child: SingleChildScrollView(
              child: SelectableText(json, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: Text(t('Cerrar', 'Close'))),
          ],
        ),
      );
      if (mounted) showSnack(context, t('Copiado: pégalo donde quieras guardarlo.', 'Copied: paste it wherever you want to keep it.'));
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    }
  }

  Future<void> _delete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t('¿Borrar tu cuenta?', 'Delete your account?')),
        content: Text(t('Se borran al momento tu cuenta, tus pedidos y todas las conversaciones. No se puede deshacer.', 'Your account, orders and all conversations are deleted right away. This can\'t be undone.')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(t('Cancelar', 'Cancel'))),
          FilledButton(
            style: FilledButton.styleFrom(
              minimumSize: const Size(0, 44),
              backgroundColor: Theme.of(context).colorScheme.error,
              foregroundColor: Theme.of(context).colorScheme.onError,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: Text(t('Borrar todo', 'Delete everything')),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await (await LaiaApi.load()).deleteAccount();
      await _logout();
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message);
    }
  }

  Future<void> _logout() async {
    await Storage.setToken(null);
    if (!mounted) return;
    Navigator.of(context, rootNavigator: true)
        .pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const AuthScreen()), (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    final user = _user;
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        Row(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: scheme.primary,
              foregroundColor: scheme.onPrimary,
              child: Text(
                (user?.firstName.isNotEmpty ?? false) ? user!.firstName[0].toUpperCase() : '🙂',
                style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(user?.name.isNotEmpty ?? false ? user!.name : t('Tu perfil', 'Your profile'),
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
                  if (user != null) Text(user.email, style: TextStyle(color: scheme.onSurfaceVariant)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        SectionTitle(t('Tus datos para las llamadas', 'Your details for calls')),
        TextField(
          controller: _name,
          textCapitalization: TextCapitalization.words,
          decoration: InputDecoration(labelText: t('Nombre', 'Name'), helperText: t('Laia dice que llama de tu parte', 'Only if the business asks')),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _address,
          minLines: 1,
          maxLines: 3,
          decoration: InputDecoration(labelText: t('Dirección de entrega', 'Delivery address'), hintText: t('Calle, número, piso, ciudad', 'Street, number, flat, city')),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _phone,
          keyboardType: TextInputType.phone,
          decoration: InputDecoration(
            labelText: t('Tu teléfono', 'Your phone'),
            helperText: t('Para el repartidor, las reservas y «Hablar yo»', 'For the courier, bookings and "Let me talk"'),
          ),
        ),
        const SizedBox(height: 16),
        FilledButton(onPressed: _saving ? null : _save, child: Text(_saving ? t('Guardando…', 'Saving…') : t('Guardar', 'Save'))),
        const SizedBox(height: 28),
        SectionTitle(t('Idioma', 'Language')),
        const LanguageSwitch(),
        const SizedBox(height: 12),
        SectionTitle(t('Avisos', 'Notifications')),
        Card(
          child: ListTile(
            leading: Icon(user?.telegramLinked ?? false ? Icons.check_circle : Icons.send,
                color: user?.telegramLinked ?? false ? scheme.tertiary : scheme.primary),
            title: Text(user?.telegramLinked ?? false ? t('Telegram conectado', 'Telegram connected') : t('Conectar Telegram', 'Connect Telegram')),
            subtitle: Text(t('Laia te avisa y te pregunta aunque tengas la app cerrada', 'Laia notifies you and asks you even with the app closed')),
            trailing: const Icon(Icons.chevron_right),
            onTap: _connectTelegram,
          ),
        ),
        const SizedBox(height: 10),
        Card(
          child: ListTile(
            leading: Icon(Icons.storefront_outlined, color: scheme.primary),
            title: Text(t('Mis sitios', 'My places')),
            subtitle: Text(t('Los negocios a los que ya has llamado o propuesto', 'Businesses you\'ve called or suggested')),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const BusinessesScreen())),
          ),
        ),
        const SizedBox(height: 28),
        SectionTitle(t('Privacidad', 'Privacy')),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: Icon(Icons.download_outlined, color: scheme.primary),
                title: Text(t('Descargar mis datos', 'Download my data')),
                onTap: _export,
              ),
              const Divider(height: 1),
              ListTile(
                leading: Icon(Icons.privacy_tip_outlined, color: scheme.primary),
                title: Text(t('Política de privacidad', 'Privacy policy')),
                trailing: const Icon(Icons.open_in_new, size: 18),
                onTap: () => _openLegal('privacidad'),
              ),
              const Divider(height: 1),
              ListTile(
                leading: Icon(Icons.gavel_outlined, color: scheme.primary),
                title: Text(t('Condiciones de uso', 'Terms of use')),
                trailing: const Icon(Icons.open_in_new, size: 18),
                onTap: () => _openLegal('terminos'),
              ),
              const Divider(height: 1),
              ListTile(
                leading: Icon(Icons.storefront, color: scheme.primary),
                title: Text(t('Información para negocios', 'Information for businesses')),
                trailing: const Icon(Icons.open_in_new, size: 18),
                onTap: () => _openLegal('negocios'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: Text(t('Avanzado', 'Advanced')),
            children: [
              TextField(
                controller: _server,
                keyboardType: TextInputType.url,
                decoration: InputDecoration(labelText: t('Servidor de Laia', 'Laia server')),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(onPressed: _logout, icon: const Icon(Icons.logout), label: Text(t('Cerrar sesión', 'Log out'))),
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: _delete,
          style: TextButton.styleFrom(foregroundColor: scheme.error),
          icon: const Icon(Icons.delete_forever_outlined),
          label: Text(t('Borrar mi cuenta', 'Delete my account')),
        ),
      ],
    );
  }
}
