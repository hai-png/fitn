/// SharedPreferences wrapper for UI state (active tab, has_onboarded, theme).
library;

import 'package:flutter/material.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

final appStatePrefsProvider =
    FutureProvider<SharedPreferences>((ref) async {
  return await SharedPreferences.getInstance();
});

final themeModeProvider = NotifierProvider<ThemeModeNotifier, ThemeMode>(
    ThemeModeNotifier.new);

class ThemeModeNotifier extends Notifier<ThemeMode> {
  @override
  ThemeMode build() {
    _load();
    return ThemeMode.system;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final s = prefs.getString('theme_mode') ?? 'system';
    state = switch (s) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> set(ThemeMode mode) async {
    state = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme_mode', mode.name);
  }
}

final unitsProvider =
    NotifierProvider<UnitsNotifier, UnitsSystem>(UnitsNotifier.new);

enum UnitsSystem { metric, imperial }

class UnitsNotifier extends Notifier<UnitsSystem> {
  @override
  UnitsSystem build() {
    _load();
    return UnitsSystem.metric;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final s = prefs.getString('units') ?? 'metric';
    state = s == 'imperial' ? UnitsSystem.imperial : UnitsSystem.metric;
  }

  Future<void> set(UnitsSystem u) async {
    state = u;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('units', u.name);
  }
}
