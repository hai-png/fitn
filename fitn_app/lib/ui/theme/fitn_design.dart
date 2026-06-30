/// Fitn design system — ported from FitLife Hub (hai-png/fitness-app).
///
/// Visual language:
/// - Colors: near-black `#1A1A1A`, cream `#F9F8F6`, red accent `#E63946`,
///   warm cream outer `#EFECE6`.
/// - Typography: Inter (sans), JetBrains Mono (mono), Playfair Display (serif
///   italic for headlines).
/// - Sharp corners (BorderRadius.zero) for cards, inputs, buttons.
/// - Uppercase tracking-widest micro-labels (10px, font-bold).
/// - Mono font for stats and numbers.
/// - Serif italic for descriptive subtitles and headlines.
/// - Phone mockup frame on desktop (410x840px, 48px rounded, 8px black border).
library;

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FitnColors {
  FitnColors._();

  /// Near-black — primary text + dark surfaces.
  static const Color ink = Color(0xFF1A1A1A);

  /// Cream — primary surface.
  static const Color cream = Color(0xFFF9F8F6);

  /// Warm cream — outer background (behind phone frame).
  static const Color warmCream = Color(0xFFEFECE6);

  /// Red accent — primary actions, highlights, active states.
  static const Color accent = Color(0xFFE63946);

  /// Darker red — hover/pressed states.
  static const Color accentDark = Color(0xFFD62828);

  /// Subtle border color.
  static const Color border = Color(0x1A1A1A1A); // ink @ 10%

  /// Subtle background fill.
  static const Color fill = Color(0xFFF9F8F6);

  // Status colors.
  static const Color success = Color(0xFF15803D);
  static const Color danger = Color(0xFFB91C1C);
  static const Color warning = Color(0xFFCA8A04);

  // Ink opacity helpers.
  static Color ink40 = const Color(0xFF1A1A1A).withOpacity(0.40);
  static Color ink50 = const Color(0xFF1A1A1A).withOpacity(0.50);
  static Color ink60 = const Color(0xFF1A1A1A).withOpacity(0.60);
  static Color ink70 = const Color(0xFF1A1A1A).withOpacity(0.70);
  static Color ink80 = const Color(0xFF1A1A1A).withOpacity(0.80);
  static Color ink05 = const Color(0xFF1A1A1A).withOpacity(0.05);
  static Color ink10 = const Color(0xFF1A1A1A).withOpacity(0.10);
  static Color ink15 = const Color(0xFF1A1A1A).withOpacity(0.15);
  static Color ink20 = const Color(0xFF1A1A1A).withOpacity(0.20);
  static Color ink30 = const Color(0xFF1A1A1A).withOpacity(0.30);

  static Color accent05 = const Color(0xFFE63946).withOpacity(0.05);
  static Color accent10 = const Color(0xFFE63946).withOpacity(0.10);
  static Color accent15 = const Color(0xFFE63946).withOpacity(0.15);
  static Color accent20 = const Color(0xFFE63946).withOpacity(0.20);
}

class FitnText {
  FitnText._();

  /// Playfair Display — italic, black weight. Used for headlines.
  static TextStyle get headline => GoogleFonts.playfairDisplay(
        fontStyle: FontStyle.italic,
        fontWeight: FontWeight.w900,
        color: FitnColors.ink,
        height: 1.05,
      );

  /// Playfair Display — italic, bold. Used for card titles.
  static TextStyle get title => GoogleFonts.playfairDisplay(
        fontStyle: FontStyle.italic,
        fontWeight: FontWeight.w700,
        color: FitnColors.ink,
      );

  /// Inter — body text.
  static TextStyle get body => GoogleFonts.inter(
        color: FitnColors.ink,
        fontSize: 13,
        height: 1.5,
      );

  /// Inter — italic body (descriptions).
  static TextStyle get bodyItalic => GoogleFonts.inter(
        color: FitnColors.ink60,
        fontStyle: FontStyle.italic,
        fontSize: 12,
        height: 1.5,
      );

  /// Playfair Display — italic descriptive text.
  static TextStyle get serifItalic => GoogleFonts.playfairDisplay(
        color: FitnColors.ink60,
        fontStyle: FontStyle.italic,
        fontSize: 12,
        height: 1.5,
      );

  /// Inter — micro-label: uppercase, tracking-widest, 10px, bold.
  static TextStyle get microLabel => GoogleFonts.inter(
        color: FitnColors.ink50,
        fontSize: 10,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.8,
      );

  /// Inter — micro-label accent (red).
  static TextStyle get microLabelAccent => GoogleFonts.inter(
        color: FitnColors.accent,
        fontSize: 10,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.8,
      );

  /// JetBrains Mono — for stats / numbers / codes.
  static TextStyle get mono => GoogleFonts.jetBrainsMono(
        color: FitnColors.ink,
        fontSize: 12,
        fontWeight: FontWeight.w600,
      );

  /// JetBrains Mono — small mono.
  static TextStyle get monoSmall => GoogleFonts.jetBrainsMono(
        color: FitnColors.ink60,
        fontSize: 10,
        fontWeight: FontWeight.w500,
  );

  /// Inter — bold uppercase button label.
  static TextStyle get buttonLabel => GoogleFonts.inter(
        color: Colors.white,
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.5,
      );
}

class FitnTheme {
  FitnTheme._();

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(
      seedColor: FitnColors.accent,
      brightness: Brightness.light,
    );
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: scheme,
      scaffoldBackgroundColor: FitnColors.cream,
      canvasColor: FitnColors.cream,
      dividerColor: FitnColors.ink10,
      textTheme: GoogleFonts.interTextTheme(ThemeData.light().textTheme),
      appBarTheme: AppBarTheme(
        backgroundColor: FitnColors.cream,
        foregroundColor: FitnColors.ink,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.playfairDisplay(
          fontStyle: FontStyle.italic,
          fontWeight: FontWeight.w900,
          fontSize: 22,
          color: FitnColors.ink,
        ),
      ),
      cardTheme: CardTheme(
        color: Colors.white,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
          side: BorderSide(color: FitnColors.ink10, width: 1),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(color: FitnColors.ink15, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(color: FitnColors.ink15, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.zero,
          borderSide: BorderSide(color: FitnColors.ink, width: 1),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        labelStyle: FitnText.microLabel,
        hintStyle: GoogleFonts.inter(color: FitnColors.ink40, fontSize: 13),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: FitnColors.ink,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48),
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.zero,
          ),
          textStyle: FitnText.buttonLabel,
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: FitnColors.ink,
          minimumSize: const Size.fromHeight(48),
          side: BorderSide(color: FitnColors.ink15, width: 1),
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.zero,
          ),
          textStyle: FitnText.buttonLabel.copyWith(color: FitnColors.ink),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: FitnColors.accent,
          textStyle: FitnText.buttonLabel.copyWith(color: FitnColors.accent),
        ),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: Colors.white.withOpacity(0.95),
        selectedItemColor: FitnColors.accent,
        unselectedItemColor: FitnColors.ink40,
        type: BottomNavigationBarType.fixed,
        showUnselectedLabels: true,
        selectedLabelStyle: GoogleFonts.inter(
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
        ),
        unselectedLabelStyle: GoogleFonts.inter(
          fontSize: 9,
          fontWeight: FontWeight.w500,
          letterSpacing: 0.8,
        ),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: FitnColors.ink,
        inactiveTrackColor: FitnColors.ink10,
        thumbColor: FitnColors.ink,
        overlayColor: FitnColors.ink05,
        trackHeight: 2,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: FitnColors.ink05,
        selectedColor: FitnColors.ink,
        labelStyle: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w600),
        side: BorderSide.none,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.zero,
        ),
      ),
      dividerTheme: DividerThemeData(
        color: FitnColors.ink10,
        thickness: 1,
        space: 1,
      ),
    );
  }
}

/// Reusable sharp-cornered card with subtle border + optional shadow.
class FitnCard extends StatelessWidget {
  const FitnCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.color = Colors.white,
    this.showShadow = true,
    this.onTap,
  });

  final Widget child;
  final EdgeInsets padding;
  final Color color;
  final bool showShadow;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            border: Border.all(color: FitnColors.ink10, width: 1),
            boxShadow: showShadow
                ? [
                    BoxShadow(
                      color: FitnColors.ink.withOpacity(0.04),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    ),
                  ]
                : null,
          ),
          child: child,
        ),
      ),
    );
  }
}

/// Section number badge — "01 —", "02 —" etc. (red, uppercase, tracking-widest).
class FitnSectionLabel extends StatelessWidget {
  const FitnSectionLabel(this.text, {super.key, this.showUnderline = true});
  final String text;
  final bool showUnderline;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: FitnText.microLabelAccent.copyWith(
          decoration: showUnderline ? TextDecoration.underline : null,
          decorationColor: FitnColors.accent,
          decorationStyle: TextDecorationStyle.solid,
          decorationThickness: 2,
        ),
      ),
    );
  }
}

/// Page title — large serif italic headline.
class FitnPageTitle extends StatelessWidget {
  const FitnPageTitle(this.text, {super.key, this.subtitle});
  final String text;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(text, style: FitnText.headline.copyWith(fontSize: 30)),
          if (subtitle != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(subtitle!, style: FitnText.serifItalic),
            ),
        ],
      ),
    );
  }
}

/// Stat tile — small uppercase label + bold value.
class FitnStatTile extends StatelessWidget {
  const FitnStatTile({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.accent = false,
  });
  final String label;
  final String value;
  final Color? valueColor;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: FitnColors.fill,
        border: Border.all(color: FitnColors.ink05, width: 1),
      ),
      child: Column(
        children: [
          Text(label.toUpperCase(),
              style: FitnText.microLabel.copyWith(fontSize: 8)),
          const SizedBox(height: 4),
          Text(
            value,
            style: FitnText.mono.copyWith(
              fontSize: 12,
              color: valueColor ?? (accent ? FitnColors.accent : FitnColors.ink),
            ),
          ),
        ],
      ),
    );
  }
}

/// Macro progress bar — label + value + horizontal bar.
class FitnMacroBar extends StatelessWidget {
  const FitnMacroBar({
    super.key,
    required this.label,
    required this.value,
    required this.percentage,
    required this.color,
  });
  final String label;
  final String value;
  final double percentage; // 0-100
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: FitnColors.ink80)),
            Text(value,
                style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: color)),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.zero,
          child: LinearProgressIndicator(
            value: (percentage / 100).clamp(0.0, 1.0),
            minHeight: 6,
            color: color,
            backgroundColor: FitnColors.fill,
          ),
        ),
      ],
    );
  }
}
