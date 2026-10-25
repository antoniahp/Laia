import 'package:flutter/material.dart';

/// Colores de Laia: índigo profundo + naranja vivo, con buen contraste en claro y en oscuro.
class LaiaColors {
  static const indigo = Color(0xFF4338CA);
  static const indigoDeep = Color(0xFF312E81);
  static const violet = Color(0xFF7C3AED);
  static const orange = Color(0xFFF2542D);
  static const orangeDeep = Color(0xFFC2410C);
  static const teal = Color(0xFF0B8466);
  static const red = Color(0xFFDC2626);
  static const ink = Color(0xFF141A2E);
  static const paper = Color(0xFFF6F7FB);
  static const night = Color(0xFF0B1020);
  static const nightCard = Color(0xFF151C33);

  /// Degradado de marca para cabeceras y la tarjeta de llamada.
  static const brandGradient = LinearGradient(
    colors: [indigoDeep, indigo, violet],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const micGradient = LinearGradient(
    colors: [Color(0xFFFF7A45), orange, Color(0xFFE23E1B)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// Para botones con texto blanco: más oscuro, para que se lea bien.
  static const ctaGradient = LinearGradient(colors: [Color(0xFFD9481A), orangeDeep]);

  static const abroadGradient = LinearGradient(
    colors: [Color(0xFF064E3B), teal, Color(0xFF0E7490)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

ThemeData laiaTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final scheme = ColorScheme.fromSeed(seedColor: LaiaColors.indigo, brightness: brightness).copyWith(
    primary: dark ? const Color(0xFFA5B4FC) : LaiaColors.indigo,
    onPrimary: dark ? const Color(0xFF1E1B4B) : Colors.white,
    primaryContainer: dark ? const Color(0xFF2E2A7A) : const Color(0xFFE0E7FF),
    onPrimaryContainer: dark ? const Color(0xFFE0E7FF) : LaiaColors.indigoDeep,
    secondary: dark ? const Color(0xFFFF8A5C) : LaiaColors.orangeDeep,
    onSecondary: dark ? const Color(0xFF3A1204) : Colors.white,
    secondaryContainer: dark ? const Color(0xFF5A2410) : const Color(0xFFFFE4D6),
    onSecondaryContainer: dark ? const Color(0xFFFFE4D6) : const Color(0xFF7C2D12),
    tertiary: dark ? const Color(0xFF5EEAD4) : LaiaColors.teal,
    onTertiary: dark ? const Color(0xFF042F2E) : Colors.white,
    tertiaryContainer: dark ? const Color(0xFF134E4A) : const Color(0xFFD1FAE5),
    onTertiaryContainer: dark ? const Color(0xFFCCFBF1) : const Color(0xFF064E3B),
    error: dark ? const Color(0xFFFCA5A5) : LaiaColors.red,
    surface: dark ? LaiaColors.nightCard : Colors.white,
    onSurface: dark ? const Color(0xFFEEF0F8) : LaiaColors.ink,
    onSurfaceVariant: dark ? const Color(0xFFB4BBD6) : const Color(0xFF4B5574),
    surfaceContainerHighest: dark ? const Color(0xFF222B47) : const Color(0xFFEDEFF6),
    outline: dark ? const Color(0xFF3A4566) : const Color(0xFFCBD0E0),
    outlineVariant: dark ? const Color(0xFF2A3352) : const Color(0xFFE2E5EF),
  );
  final radius = BorderRadius.circular(16);
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: dark ? LaiaColors.night : LaiaColors.paper,
    appBarTheme: AppBarTheme(
      backgroundColor: dark ? LaiaColors.night : LaiaColors.paper,
      foregroundColor: scheme.onSurface,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: scheme.onSurface),
    ),
    cardTheme: CardThemeData(
      color: scheme.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: radius, side: BorderSide(color: scheme.outlineVariant)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: scheme.surface,
      border: OutlineInputBorder(borderRadius: radius, borderSide: BorderSide(color: scheme.outline)),
      enabledBorder: OutlineInputBorder(borderRadius: radius, borderSide: BorderSide(color: scheme.outline)),
      focusedBorder: OutlineInputBorder(borderRadius: radius, borderSide: BorderSide(color: scheme.primary, width: 2)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(54),
        shape: RoundedRectangleBorder(borderRadius: radius),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(50),
        shape: RoundedRectangleBorder(borderRadius: radius),
        side: BorderSide(color: scheme.outline),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
      ),
    ),
    chipTheme: ChipThemeData(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      side: BorderSide(color: scheme.outline),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: scheme.surface,
      indicatorColor: scheme.primaryContainer,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 12,
          fontWeight: states.contains(WidgetState.selected) ? FontWeight.w700 : FontWeight.w500,
        ),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
  );
}
