/// Engine-level error types.

/// Thrown by [FitnEngine.proposePlan] when the [AssessmentResult] passed to it
/// has `isPartial == true`. The engine refuses to build a plan on top of a
/// partial assessment — the UI must check `assessment.isPartial` first and
/// surface a "regenerate" CTA instead of attempting plan generation.
class PartialAssessmentError implements Exception {
  PartialAssessmentError(this.errors);

  /// The list of `"sub_name: ArgumentError: <msg>"` strings captured by the
  /// assessor. Each one represents a sub-assessment that failed.
  final List<String> errors;

  /// Human-readable join of [errors].
  String get message =>
      errors.isEmpty
          ? 'Assessment is partial.'
          : 'Assessment is partial: ${errors.join('; ')}';

  @override
  String toString() => 'PartialAssessmentError: $message';
}

/// Thrown by [FitnEngine] when an internal invariant is violated in a way that
/// should never happen for valid inputs. Surfacing this to the user indicates
/// an engine bug.
class EngineStateError implements Exception {
  EngineStateError(this.message);
  final String message;
  @override
  String toString() => 'EngineStateError: $message';
}
