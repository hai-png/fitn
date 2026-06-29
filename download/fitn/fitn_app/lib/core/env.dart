/// Environment variables (Supabase URL/anon key).
///
/// The anon key is safe to ship in the app — it's protected by RLS policies.
/// Replace with your own Supabase project credentials.
library;

class Env {
  const Env._();

  /// Supabase project URL.
  ///
  /// Replace with your project URL from supabase.com dashboard.
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://YOUR-PROJECT.supabase.co',
  );

  /// Supabase anon (public) key.
  ///
  /// Safe to ship — protected by RLS. Replace with your project's anon key.
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'YOUR-ANON-KEY',
  );

  /// Deep-link scheme for OAuth/magic-link callbacks.
  static const String deepLinkScheme = 'com.fitn.app';

  /// Quick check whether Supabase is configured.
  static bool get isSupabaseConfigured =>
      !supabaseUrl.contains('YOUR-PROJECT') &&
      !supabaseAnonKey.contains('YOUR-ANON-KEY');
}
