/// Generic enum helpers. Each concrete enum also has its own `fromJson` /
/// `toJson` and display helpers in `models/enums.dart`.

/// Convert a snake_case string to a camelCase Dart enum value name.
///
/// Most wire forms are snake_case (e.g. `"mostly_sedentary"`); the in-Dart
/// enum is camelCase (`mostlySedentary`). Use this to bridge.
String snakeToCamel(String s) {
  if (s.isEmpty) return s;
  final out = StringBuffer();
  var cap = false;
  for (final ch in s.split('')) {
    if (ch == '_') {
      cap = true;
    } else {
      out.write(cap ? ch.toUpperCase() : ch);
      cap = false;
    }
  }
  return out.toString();
}

/// Convert a camelCase Dart enum value name back to snake_case wire form.
String camelToSnake(String s) {
  final out = StringBuffer();
  for (final ch in s.split('')) {
    if (ch.toUpperCase() == ch && ch.toLowerCase() != ch) {
      out.write('_');
      out.write(ch.toLowerCase());
    } else {
      out.write(ch);
    }
  }
  return out.toString();
}

/// Look up an enum value by its name (camelCase or snake_case).
T enumFromString<T extends Enum>(List<T> values, String name) {
  final camel = snakeToCamel(name);
  for (final v in values) {
    if (v.name == camel) return v;
  }
  throw ArgumentError('Unknown $T: "$name"');
}

/// Convert an enum value to its snake_case wire form.
String enumToJson<T extends Enum>(T value) => camelToSnake(value.name);

/// Capitalize the first letter of a string.
String capitalize(String s) =>
    s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

/// Capitalize the first letter of each word.
String titleCase(String s) =>
    s.split(' ').map(capitalize).join(' ');

/// Lowercase the first letter of a string.
String decapitalize(String s) =>
    s.isEmpty ? s : s[0].toLowerCase() + s.substring(1);

/// Pretty-print an enum value: `veryConservative` → `Very Conservative`.
String enumToDisplay<T extends Enum>(T value) {
  final out = StringBuffer();
  for (final ch in value.name.split('')) {
    if (ch.toUpperCase() == ch && ch.toLowerCase() != ch) {
      out.write(' ');
    }
    out.write(ch);
  }
  final s = out.toString();
  return s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);
}
