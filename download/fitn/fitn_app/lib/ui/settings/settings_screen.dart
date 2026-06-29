/// Settings screen. See spec §7.11.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/env.dart';
import '../../data/prefs/app_state_provider.dart';
import '../../state/app_state.dart';
import '../../theme/app_theme.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final units = ref.watch(unitsProvider);
    final sync = ref.watch(syncProvider);
    final auth = ref.watch(authNotifierProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: ListView(
          children: [
            const _SectionHeader('Appearance'),
            ListTile(
              leading: const Icon(LucideIcons.sunMoon),
              title: const Text('Theme'),
              trailing: DropdownButton<ThemeMode>(
                value: themeMode,
                underline: const SizedBox(),
                items: const [
                  DropdownMenuItem(
                      value: ThemeMode.system, child: Text('System')),
                  DropdownMenuItem(
                      value: ThemeMode.light, child: Text('Light')),
                  DropdownMenuItem(
                      value: ThemeMode.dark, child: Text('Dark')),
                ],
                onChanged: (m) {
                  if (m != null) {
                    ref.read(themeModeProvider.notifier).set(m);
                  }
                },
              ),
            ),
            ListTile(
              leading: const Icon(LucideIcons.ruler),
              title: const Text('Units'),
              trailing: DropdownButton<UnitsSystem>(
                value: units,
                underline: const SizedBox(),
                items: const [
                  DropdownMenuItem(
                      value: UnitsSystem.metric, child: Text('Metric')),
                  DropdownMenuItem(
                      value: UnitsSystem.imperial, child: Text('Imperial')),
                ],
                onChanged: (u) {
                  if (u != null) {
                    ref.read(unitsProvider.notifier).set(u);
                  }
                },
              ),
            ),
            const Divider(),
            const _SectionHeader('Sync'),
            if (!Env.isSupabaseConfigured)
              const ListTile(
                leading: Icon(LucideIcons.cloudOff, color: AppColors.warning),
                title: Text('Sync not configured'),
                subtitle: Text(
                    'Add SUPABASE_URL and SUPABASE_ANON_KEY to enable sync.'),
              )
            else ...[
              ListTile(
                leading: const Icon(LucideIcons.cloud),
                title: Text(auth.isAuthenticated
                    ? 'Signed in as ${auth.email}'
                    : 'Not signed in'),
                subtitle: Text(sync.lastSyncAt != null
                    ? 'Last sync: ${sync.lastSyncAt}'
                    : 'Never synced'),
                trailing: sync.isFlushing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : null,
              ),
              ListTile(
                leading: const Icon(LucideIcons.refreshCw),
                title: const Text('Sync now'),
                subtitle: Text('${sync.queueLength} pending'),
                onTap: () => ref.read(syncProvider.notifier).flush(),
              ),
              if (auth.isAuthenticated)
                ListTile(
                  leading: const Icon(LucideIcons.logOut, color: AppColors.danger),
                  title: const Text('Sign out',
                      style: TextStyle(color: AppColors.danger)),
                  onTap: () => ref.read(authNotifierProvider.notifier).signOut(),
                ),
            ],
            const Divider(),
            const _SectionHeader('About'),
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
            const ListTile(
              leading: Icon(LucideIcons.fileText),
              title: Text('Terms of service'),
              trailing: Icon(LucideIcons.chevronRight),
            ),
            const Divider(),
            const _SectionHeader('Danger Zone'),
            ListTile(
              leading:
                  const Icon(LucideIcons.trash2, color: AppColors.danger),
              title: const Text('Clear all local data',
                  style: TextStyle(color: AppColors.danger)),
              onTap: () => _confirmClear(context, ref),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmClear(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Clear all data?'),
          content: const Text(
              'This permanently deletes your profile, plans, workout logs, weight logs, and intake logs from this device. This cannot be undone.'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.danger),
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Clear all'),
            ),
          ],
        );
      },
    );
    if (confirmed == true) {
      // Re-confirm.
      if (!context.mounted) return;
      final confirmed2 = await showDialog<bool>(
        context: context,
        builder: (context) {
          return AlertDialog(
            title: const Text('Are you absolutely sure?'),
            content: const Text('Type nothing — just tap "Clear all" again.'),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Cancel')),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.danger),
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Clear all'),
              ),
            ],
          );
        },
      );
      if (confirmed2 == true) {
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
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
          color: AppColors.textSecondaryDark,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
