/// Auth screens. See spec §7.10.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/env.dart';
import '../../state/app_state.dart';
import '../../theme/app_theme.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});

  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  final _emailCtrl = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sign in')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(LucideIcons.dumbbell, size: 48, color: AppColors.primary),
              const SizedBox(height: 16),
              const Text('Sign in to sync across devices',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              const Text(
                'Your plan stays on your device. Sign-in only syncs across devices.',
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: AppColors.textSecondaryDark, fontSize: 13),
              ),
              const SizedBox(height: 24),
              if (!_sent) ...[
                TextField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(LucideIcons.mail),
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _sendMagicLink,
                  icon: const Icon(LucideIcons.send),
                  label: const Text('Send magic link'),
                ),
              ] else ...[
                const Icon(LucideIcons.mailCheck, size: 48, color: AppColors.success),
                const SizedBox(height: 16),
                Text(
                  'Check your email at ${_emailCtrl.text} for a sign-in link.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => setState(() => _sent = false),
                  child: const Text('Use a different email'),
                ),
              ],
              const SizedBox(height: 24),
              if (Env.isSupabaseConfigured) ...[
                const Row(
                  children: [
                    Expanded(child: Divider()),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 8),
                      child: Text('or',
                          style: TextStyle(
                              color: AppColors.textSecondaryDark)),
                    ),
                    Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(authNotifierProvider.notifier)
                      .signInWithOAuth('google'),
                  icon: const Icon(LucideIcons.chrome),
                  label: const Text('Continue with Google'),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(authNotifierProvider.notifier)
                      .signInWithOAuth('apple'),
                  icon: const Icon(LucideIcons.apple),
                  label: const Text('Continue with Apple'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _sendMagicLink() async {
    if (_emailCtrl.text.isEmpty) return;
    try {
      await ref
          .read(authNotifierProvider.notifier)
          .signInWithMagicLink(_emailCtrl.text);
      setState(() => _sent = true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to send magic link: $e')),
        );
      }
    }
  }
}

class AuthCallbackScreen extends ConsumerWidget {
  const AuthCallbackScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // The Supabase SDK handles the actual session restoration in
    // authNotifierProvider's onAuthStateChange listener. We just show a
    // loading state and pop back home.
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            const Text('Completing sign-in…'),
            TextButton(
              onPressed: () => Navigator.of(context).goNamed('/'),
              child: const Text('Continue'),
            ),
          ],
        ),
      ),
    );
  }
}

extension on NavigatorState {
  void goNamed(String name) {
    // Simplified — real implementation uses go_router's context.go.
    popUntil((route) => route.isFirst);
  }
}
