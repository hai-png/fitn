/// Result<T> sealed class — discriminated union for success/failure.
library;

sealed class Result<T> {
  const Result();
  factory Result.success(T value) = Success<T>;
  factory Result.failure(String message, [Object? error]) = Failure<T>;
  factory Result.from(T Function() fn) {
    try {
      return Result.success(fn());
    } catch (e) {
      return Result.failure(e.toString(), e);
    }
  }

  /// `true` for [Success], `false` for [Failure].
  bool get isSuccess => switch (this) {
        Success<T>() => true,
        Failure<T>() => false,
      };

  /// Get the success value, or throw if [Failure].
  T getOrThrow() => switch (this) {
        Success(:final value) => value,
        Failure(:final message) => throw Exception(message),
      };

  /// Get the success value, or null if [Failure].
  T? getOrNull() => switch (this) {
        Success(:final value) => value,
        Failure() => null,
      };

  /// Map the success value.
  Result<U> map<U>(U Function(T) fn) => switch (this) {
        Success(:final value) => Result.success(fn(value)),
        Failure(:final message, :final error) =>
          Result.failure(message, error),
      };
}

final class Success<T> extends Result<T> {
  const Success(this.value);
  final T value;
}

final class Failure<T> extends Result<T> {
  const Failure(this.message, [this.error]);
  final String message;
  final Object? error;
}
