/// App bootstrap. Initializes Supabase + engine data + sync.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'core/env.dart';
import 'engine/engine_provider.dart';

class AppBootstrap {
  AppBootstrap._();

  /// Initialize everything that needs to happen before runApp.
  static Future<Container> init() async {
    final container = ProviderContainer();

    // Initialize Supabase (only if configured).
    if (Env.isSupabaseConfigured) {
      try {
        await Supabase.initialize(
          url: Env.supabaseUrl,
          anonKey: Env.supabaseAnonKey,
          debug: kDebugMode,
        );
      } catch (e) {
        if (kDebugMode) {
          debugPrint('Supabase init failed (continuing without sync): $e');
        }
      }
    }

    // Pre-load engine data so the first plan generation is instant.
    try {
      await getEngineData();
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Engine data load failed: $e');
      }
    }

    return container;
  }
}
