// Basic smoke test — verifies the app builds and the FitnApp widget renders.
//
// To run: `flutter test`

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fitn_app/app.dart';

void main() {
  testWidgets('App renders without crashing', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: FitnApp(),
      ),
    );

    // The app should render — we just verify no exception is thrown.
    // (Full widget tree verification would require mocking engine data load.)
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(FitnApp), findsOneWidget);
  });
}
