/// Internal JSON helpers shared across models.

double? optDouble(Object? v) => v == null ? null : (v as num).toDouble();

double reqDouble(Object v) => (v as num).toDouble();

int? optInt(Object? v) => v == null ? null : (v as num).toInt();

int reqInt(Object v) => (v as num).toInt();

bool? optBool(Object? v) => v == null ? null : v == true;

bool reqBool(Object v) => v == true;

String? optString(Object? v) => v == null ? null : v.toString();

String reqString(Object v) => v.toString();

List<double> doubleList(Object? v) {
  if (v == null) return const [];
  if (v is! List) return const [];
  return v.map((e) => (e as num).toDouble()).toList();
}

List<int> intList(Object? v) {
  if (v == null) return const [];
  if (v is! List) return const [];
  return v.map((e) => (e as num).toInt()).toList();
}

List<String> stringList(Object? v) {
  if (v == null) return const [];
  if (v is! List) return const [];
  return v.map((e) => e.toString()).toList();
}

Map<String, double> doubleMap(Object? v) {
  if (v == null) return {};
  if (v is! Map) return {};
  return v.map((k, val) => MapEntry(k.toString(), (val as num).toDouble()));
}

Map<String, dynamic> dynamicMap(Object? v) {
  if (v == null) return {};
  if (v is! Map) return {};
  return v.map((k, val) => MapEntry(k.toString(), val as dynamic));
}

bool listEquals<T>(List<T>? a, List<T>? b) {
  if (identical(a, b)) return true;
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

bool mapEquals<K, V>(Map<K, V>? a, Map<K, V>? b) {
  if (identical(a, b)) return true;
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (final k in a.keys) {
    if (!b.containsKey(k) || a[k] != b[k]) return false;
  }
  return true;
}
