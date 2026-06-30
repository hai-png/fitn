/// Engine version stamp. Bumped on any engine logic change.
///
/// Every [FitnessPlan] produced by this engine carries this string in its
/// `engineVersion` field so the app can detect stale plans and offer to
/// regenerate them.
const String engineVersion = '3.2.0';
