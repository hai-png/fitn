/// Common reusable widgets: ProgressRing, AnimatedNumber, MacroRing, Skeleton.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../theme/app_theme.dart';

class ProgressRing extends StatelessWidget {
  const ProgressRing({
    super.key,
    required this.progress,
    this.size = 80,
    this.strokeWidth = 8,
    this.color = AppColors.primary,
    this.child,
  });

  final double progress; // 0.0 - 1.0
  final double size;
  final double strokeWidth;
  final Color color;
  final Widget? child;

  @override
  Widget build(BuildContext context) {
    final clamped = progress.clamp(0.0, 1.0);
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: 1,
            strokeWidth: strokeWidth,
            color: color.withValues(alpha: 0.15),
          ),
          CircularProgressIndicator(
            value: clamped,
            strokeWidth: strokeWidth,
            color: color,
            backgroundColor: Colors.transparent,
          ).animate().fade(duration: 600.ms),
          if (child != null) child!,
        ],
      ),
    );
  }
}

class AnimatedNumber extends StatelessWidget {
  const AnimatedNumber({
    super.key,
    required this.value,
    this.suffix = '',
    this.prefix = '',
    this.fractionDigits = 0,
    this.style,
  });

  final double value;
  final String suffix;
  final String prefix;
  final int fractionDigits;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: value),
      duration: 800.ms,
      curve: Curves.easeOutCubic,
      builder: (context, v, _) {
        return Text(
          '$prefix${v.toStringAsFixed(fractionDigits)}$suffix',
          style: style,
        );
      },
    );
  }
}

class MacroRing extends StatelessWidget {
  const MacroRing({
    super.key,
    required this.label,
    required this.current,
    required this.target,
    required this.unit,
    required this.color,
  });

  final String label;
  final double current;
  final double target;
  final String unit;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final progress = target > 0 ? (current / target).clamp(0.0, 1.0) : 0.0;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ProgressRing(
          progress: progress,
          size: 64,
          strokeWidth: 6,
          color: color,
          child: Text(
            '${(progress * 100).round()}%',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimaryDark,
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: AppColors.textSecondaryDark,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '${current.round()} / ${target.round()} $unit',
          style: const TextStyle(
            fontSize: 11,
            color: AppColors.textPrimaryDark,
          ),
        ),
      ],
    );
  }
}

class Skeleton extends StatelessWidget {
  const Skeleton({
    super.key,
    this.width,
    this.height = 16,
    this.borderRadius = 8,
  });

  final double? width;
  final double height;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.bgDarkSurface,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .shimmer(duration: 1200.ms, color: Colors.white.withValues(alpha: 0.04));
  }
}

class SkeletonCard extends StatelessWidget {
  const SkeletonCard({super.key, this.lines = 3});

  final int lines;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Skeleton(width: 120, height: 18),
            const SizedBox(height: 12),
            for (var i = 0; i < lines; i++) ...[
              Skeleton(width: i == lines - 1 ? 180 : double.infinity),
              if (i < lines - 1) const SizedBox(height: 8),
            ],
          ],
        ),
      ),
    );
  }
}

class Haptics {
  Haptics._();

  static Future<void> selectionClick() async {
    // Flutter's HapticFeedback requires flutter/services — imported via material.
    // Skipped for skeleton simplicity.
  }

  static Future<void> mediumImpact() async {}

  static Future<void> heavyImpact() async {}
}
