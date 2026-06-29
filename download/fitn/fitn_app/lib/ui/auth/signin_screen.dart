/// Auth screens — magic-link + OAuth. Matches FitLife Hub design.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/env.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

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
      backgroundColor: FitnColors.cream,
      appBar: AppBar(title: const Text('Sign in')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Icon(LucideIcons.dumbbell, size: 48, color: FitnColors.accent),
              const SizedBox(height: 16),
              Text('Sign in to sync across devices',
                  textAlign: TextAlign.center,
                  style: FitnText.headline.copyWith(fontSize: 20)),
              const SizedBox(height: 8),
              Text(
                'Your plan stays on your device. Sign-in only syncs across devices.',
                textAlign: TextAlign.center,
                style: FitnText.serifItalic,
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
                  icon: Icon(LucideIcons.send, size: 16, color: Colors.white),
                  label: Text('SEND MAGIC LINK', style: FitnText.buttonLabel),
                ),
              ] else ...[
                Icon(LucideIcons.mailCheck, size: 48, color: FitnColors.accent),
                const SizedBox(height: 16),
                Text(
                  'Check your email at ${_emailCtrl.text} for a sign-in link.',
                  textAlign: TextAlign.center,
                  style: FitnText.body,
                ),
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => setState(() => _sent = false),
                  child: Text('USE A DIFFERENT EMAIL',
                      style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.0,
                          color: FitnColors.ink)),
                ),
              ],
              const SizedBox(height: 24),
              if (Env.isSupabaseConfigured) ...[
                Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      child: Text('or',
                          style: GoogleFonts.inter(
                              color: FitnColors.ink40, fontSize: 11)),
                    ),
                    const Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(authNotifierProvider.notifier)
                      .signInWithOAuth('google'),
                  icon: Icon(LucideIcons.chrome, size: 16),
                  label: Text('CONTINUE WITH GOOGLE',
                      style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.0,
                          color: FitnColors.ink)),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => ref
                      .read(authNotifierProvider.notifier)
                      .signInWithOAuth('apple'),
                  icon: Icon(LucideIcons.apple, size: 16),
                  label: Text('CONTINUE WITH APPLE',
                      style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.0,
                          color: FitnColors.ink)),
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
    ref.listen(authNotifierProvider, (previous, next) {
      if (next.isAuthenticated) {
        context.go('/');
      }
    });

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: FitnColors.accent),
            const SizedBox(height: 16),
            Text('Completing sign-in...', style: FitnText.body),
            const SizedBox(height: 24),
            TextButton(
              onPressed: () => context.go('/'),
              child: Text('CONTINUE TO APP',
                  style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                      color: FitnColors.accent)),
            ),
          ],
        ),
      ),
    );
  }
}
