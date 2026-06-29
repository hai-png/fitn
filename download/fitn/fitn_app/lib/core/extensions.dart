/// DateTime + num extensions.
library;

extension DateTimeX on DateTime {
  /// `yyyy-MM-dd`.
  String get ymd {
    final y = year.toString();
    final m = month.toString().padLeft(2, '0');
    final d = day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  /// `HH:mm`.
  String get hm {
    final h = hour.toString().padLeft(2, '0');
    final m = minute.toString().padLeft(2, '0');
    return '$h:$m';
  }

  /// Days since [other].
  int daysSince(DateTime other) {
    final a = DateTime(year, month, day);
    final b = DateTime(other.year, other.month, other.day);
    return a.difference(b).inDays;
  }

  /// Whether this is the same calendar day as [other].
  bool isSameDay(DateTime other) =>
      year == other.year && month == other.month && day == other.day;

  /// 1 = Monday, 7 = Sunday.
  int get isoWeekday => weekday;
}

extension NumX on num {
  /// Round to [decimals] places using toStringAsFixed.
  String toFixed(int decimals) => toStringAsFixed(decimals);

  /// `true` if this is between [min] and [max] (inclusive).
  bool inRange(num min, num max) => this >= min && this <= max;

  /// Clamp into [min, max] (returns num to preserve type).
  num clampTo(num min, num max) => clamp(min, max);
}

extension DoubleX on double {
  /// Format as integer with thousands separator.
  String get thousandsSeparated {
    final s = round().toString();
    final buf = StringBuffer();
    for (var i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
      buf.write(s[i]);
    }
    return buf.toString();
  }
}

extension IntX on int {
  /// Format as integer with thousands separator.
  String get thousandsSeparated {
    final s = toString();
    final buf = StringBuffer();
    for (var i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
      buf.write(s[i]);
    }
    return buf.toString();
  }
}
