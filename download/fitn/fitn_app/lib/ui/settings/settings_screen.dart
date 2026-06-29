/// Settings screen — matches FitLife Hub design.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/env.dart';
import '../../data/prefs/app_state_provider.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final units = ref.watch(unitsProvider);
    final sync = ref.watch(syncProvider);
    final auth = ref.watch(authNotifierProvider);

    return Scaffold(
      backgroundColor: FitnColors.cream,
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: ListView(
          children: [
            _section('APPEARANCE'),
            ListTile(
              leading: Icon(LucideIcons.sunMoon, color: FitnColors.ink),
              title: Text('Theme', style: GoogleFonts.inter(fontSize: 13)),
              trailing: DropdownButton<ThemeMode>(
                value: themeMode,
                underline: const SizedBox(),
                style: GoogleFonts.inter(fontSize: 12, color: FitnColors.ink),
                items: const [
                  DropdownMenuItem(value: ThemeMode.system, child: Text('System')),
                  DropdownMenuItem(value: ThemeMode.light, child: Text('Light')),
                  DropdownMenuItem(value: ThemeMode.dark, child: Text('Dark')),
                ],
                onChanged: (m) {
                  if (m != null) ref.read(themeModeProvider.notifier).set(m);
                },
              ),
            ),
            ListTile(
              leading: Icon(LucideIcons.ruler, color: FitnColors.ink),
              title: Text('Units', style: GoogleFonts.inter(fontSize: 13)),
              trailing: DropdownButton<UnitsSystem>(
                value: units,
                underline: const SizedBox(),
                style: GoogleFonts.inter(fontSize: 12, color: FitnColors.ink),
                items: const [
                  DropdownMenuItem(value: UnitsSystem.metric, child: Text('Metric')),
                  DropdownMenuItem(value: UnitsSystem.imperial, child: Text('Imperial')),
                ],
                onChanged: (u) {
                  if (u != null) ref.read(unitsProvider.notifier).set(u);
                },
              ),
            ),
            const Divider(),
            _section('SYNC'),
            if (!Env.isSupabaseConfigured)
              const ListTile(
                leading: Icon(LucideIcons.cloudOff, color: FitnColors.warning),
                title: Text('Sync not configured'),
                subtitle: Text(
                    'Add SUPABASE_URL and SUPABASE_ANON_KEY to enable sync.'),
              )
            else ...[
              ListTile(
                leading: Icon(LucideIcons.cloud, color: FitnColors.ink),
                title: Text(auth.isAuthenticated
                    ? 'Signed in as ${auth.email}'
                    : 'Not signed in', style: GoogleFonts.inter(fontSize: 13)),
                subtitle: Text(sync.lastSyncAt != null
                    ? 'Last sync: ${sync.lastSyncAt}'
                    : 'Never synced', style: GoogleFonts.inter(fontSize: 11)),
                trailing: sync.isFlushing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : null,
              ),
              ListTile(
                leading: Icon(LucideIcons.refreshCw, color: FitnColors.ink),
                title: Text('Sync now', style: GoogleFonts.inter(fontSize: 13)),
                subtitle: Text('${sync.queueLength} pending',
                    style: GoogleFonts.inter(fontSize: 11)),
                onTap: () => ref.read(syncProvider.notifier).flush(),
              ),
              if (auth.isAuthenticated)
                ListTile(
                  leading: Icon(LucideIcons.logOut, color: FitnColors.danger),
                  title: Text('Sign out',
                      style: GoogleFonts.inter(
                          fontSize: 13, color: FitnColors.danger)),
                  onTap: () => ref.read(authNotifierProvider.notifier).signOut(),
                ),
            ],
            const Divider(),
            _section('ABOUT'),
            const ListTile(
              leading: Icon(LucideIcons.info),
              title: Text('Engine version'),
              trailing: Text('3.2.0'),
            ),
            const ListTile(
              leading: Icon(LucideIcons.shield),
              title: Text('Privacy policy'),
              trailing: Icon(LucideIcons.chevronRight),
            ),
            const Divider(),
            _section('DANGER ZONE'),
            ListTile(
              leading: Icon(LucideIcons.trash2, color: FitnColors.danger),
              title: Text('Clear all local data',
                  style: GoogleFonts.inter(
                      fontSize: 13, color: FitnColors.danger)),
              onTap: () => _confirmClear(context, ref),
            ),
          ],
        ),
      ),
    );
  }

  Widget _section(String text) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        text,
        style: GoogleFonts.inter(
            color: FitnColors.ink50,
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.4),
      ),
    );
  }

  Future<void> _confirmClear(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Clear all data?',
            style: FitnText.headline.copyWith(fontSize: 18)),
        content: Text(
            'This permanently deletes your profile, plans, workout logs, weight logs, and intake logs from this device. This cannot be undone.',
            style: FitnText.body),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: FitnColors.danger),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Clear all'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(profileRepoProvider).clear();
      await ref.read(weightLogRepoProvider).clear();
      await ref.read(intakeLogRepoProvider).clear();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('All local data cleared.')),
        );
      }
    }
  }
}
