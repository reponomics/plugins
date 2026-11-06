# Coverage beyond Python and JavaScript

Start with the project's existing tests; a new framework or a high initial percentage is not a prerequisite for a useful report. Read the recipe for the project's language, then follow [reporting.md](reporting.md) to publish the report and add a badge. Preserve the existing test framework.

Keep the project's compiler, package manager, wrappers, and test selection. Add coverage tooling through its existing development-tool configuration, and record the chosen version. These are starting recipes, not replacements for project-specific integration tests or platform builds. Upstream guidance was checked on 2026-10-31; check compatibility with the installed versions when adopting them.

## Choose a report

The [coverage-tool license table](licenses.md) lists each tool's license and OSI approval status, including the differences between Swift tooling and Xcode, and between PHP coverage drivers.

| Project | Good first tool | Report to upload | What to inspect |
| --- | --- | --- | --- |
| Go | Built-in `go test` | `coverage.out` (Go text) | Statements and packages included |
| Rust | `cargo-llvm-cov` | `lcov.info` | Lines/regions; features and workspace members |
| Java / Kotlin JVM | JaCoCo with the existing Gradle/Maven build | `jacocoTestReport.xml` / `jacoco.xml` | Lines, bytecode instructions, and branches separately |
| C# / .NET | Coverlet integration matching the test runner | `coverage.cobertura.xml` | Lines, branches, and included assemblies |
| C / C++ | GCC coverage plus gcovr, or existing LLVM tooling | Cobertura XML / LCOV | Compiled source set and compiler-generated branches |
| Swift | SwiftPM/Xcode coverage plus LLVM export | LCOV | Production files and tested platform |
| Ruby | SimpleCov plus LCOV or Cobertura formatter | Formatter's LCOV / Cobertura file | Files loaded before coverage starts |
| PHP | PHPUnit plus PCOV or Xdebug | Clover XML | Source inclusion and coverage driver |

[Codecov accepts these report formats](https://docs.codecov.com/docs/supported-report-formats). Upload the generated text/XML report; HTML is for readers. Raw JaCoCo `.exec`, Xcode `.xccov`, and SimpleCov's current JSON output are not suitable uploads. An `.xml` extension alone does not identify a coverage format: JUnit XML describes test results, not coverage.

## Go: no extra coverage package

Run from the module root with the project's Go toolchain:

```sh
go test ./... -coverpkg=./... -covermode=atomic -coverprofile=coverage.out
go tool cover -func=coverage.out
go tool cover -html=coverage.out -o coverage.html
```

`-coverpkg=./...` measures packages across the current module when tests call into them. Check the report for packages with no tests; nested modules require their own runs. Preserve existing build tags and test flags. Go reports **statement coverage**, not branch coverage; a green line does not prove both sides of every condition ran. Application/integration-test coverage has a separate instrumented-build workflow. See [Go's coverage guide](https://go.dev/doc/build-cover) and [coverage metrics](https://go.dev/blog/cover).

## Rust: keep Cargo and the existing feature set

Install `cargo-llvm-cov` using the project's tool-management convention. With rustup, add the `llvm-tools-preview` component to the toolchain the project uses; other installations need compatible LLVM tools. Then:

```sh
cargo llvm-cov --workspace --lcov --output-path lcov.info
cargo llvm-cov report --html
```

The second command renders the collected data under `target/llvm-cov/html`; it does not rerun tests. Preserve the normal feature flags rather than automatically adding `--all-features`, since features can be mutually exclusive. Inspect production paths and untested workspace members. Line and region coverage work on stable Rust; optional branch coverage and doctest coverage currently require nightly. Do not describe a stable-toolchain line result as branch coverage. See [cargo-llvm-cov's prerequisites, commands, and limitations](https://github.com/taiki-e/cargo-llvm-cov).

## Java / Kotlin JVM: add reporting to the existing build

For a conventional Gradle JVM project, merge this into `build.gradle.kts`, preserving its existing plugins:

```kotlin
plugins {
    jacoco
}

tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
    }
}
```

Run `./gradlew test jacocoTestReport`; upload `build/reports/jacoco/test/jacocoTestReport.xml` and open the sibling `html/index.html`. Use the equivalent syntax for an existing Groovy build. Multi-project builds need per-project reports or an aggregation task; Android uses variant-specific test tasks. Reuse Kover if the Kotlin project already has it. See [Gradle's JaCoCo integration](https://docs.gradle.org/current/userguide/jacoco_plugin.html).

For Maven, configure a released, Java-compatible `jacoco-maven-plugin` version with `prepare-agent` and `report` executions (`report` at `verify`), then run `./mvnw verify`. The normal report is `target/site/jacoco/jacoco.xml`. Preserve existing Surefire/Failsafe JVM arguments so the agent is retained; do not disable test forking. See [JaCoCo's Maven setup and sample POM](https://www.jacoco.org/jacoco/trunk/doc/maven.html).

JaCoCo measures bytecode instructions, lines, and branches; instruction coverage is not source statement coverage. Its branch counter excludes exception handling. Keep debug information for source-line mapping, and inspect Kotlin-generated code before interpreting missed branches. See [JaCoCo counter definitions](https://www.jacoco.org/jacoco/trunk/doc/counters.html).

## C# / .NET: identify the test runner first

For an SDK-style test project using **VSTest**, add or reuse the `coverlet.collector` package in the test project, then run:

```sh
dotnet test --collect:"XPlat Code Coverage" --results-directory TestResults
```

Upload the generated `TestResults/<run-id>/coverage.cobertura.xml` files from that run. The collector needs compatible .NET SDK and `Microsoft.NET.Test.Sdk` versions; consult the selected package release's requirements. Confirm that production assemblies, including untested ones, appear in the report.

For **Microsoft.Testing.Platform**, use its compatible coverage extension instead: `coverlet.collector` is a VSTest integration. Current Coverlet documents `coverlet.MTP` with `dotnet test --coverlet`; verify support in the released package being installed and request Cobertura output. Keep the existing runner. See [Coverlet integrations and compatibility](https://github.com/coverlet-coverage/coverlet).

## C / C++: instrument the build before running tests

For an existing CMake/CTest project using GCC, a separate coverage build keeps instrumentation out of release builds. Install gcovr through the existing tooling environment and use the `gcov` matching the compiler:

```sh
cmake -S . -B build-coverage -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="--coverage" -DCMAKE_CXX_FLAGS="--coverage"
cmake --build build-coverage
ctest --test-dir build-coverage --output-on-failure --no-tests=error
gcovr --root . build-coverage --filter 'src/' --cobertura coverage.xml
```

Replace `src/` with all production source directories, including owned headers. Preserve existing compiler/linker flags and the project's option for enabling tests. Start from a fresh coverage build for each baseline. GCC's coverage flags must reach compilation and linking; Clang/Apple Clang need their matching LLVM coverage tools instead. For another build system, keep it and add equivalent instrumentation. See [gcovr's CMake recipe](https://gcovr.com/en/stable/cookbook.html) and [Cobertura export](https://gcovr.com/en/stable/output/cobertura.html).

## Swift: start with the package's tests

For a Swift package, run `swift test --enable-code-coverage`. SwiftPM writes coverage data under its build directory; `swift test --show-codecov-path` prints its JSON report location. For a Codecov upload, export LCOV using the instrumented test binary and matching profile. On macOS, a conventional XCTest package can use:

```sh
xcrun llvm-cov export -format=lcov \
  -ignore-filename-regex='(^|/)(Tests|\.build)/' \
  -instr-profile=.build/debug/codecov/default.profdata \
  .build/debug/YourPackagePackageTests.xctest/Contents/MacOS/YourPackagePackageTests \
  > lcov.info
```

Replace the binary path with the actual test product from the build; Linux uses an executable rather than the macOS bundle layout and needs the Swift toolchain's compatible `llvm-cov`. Filter test/generated/dependency paths consistently and inspect production coverage. For an Xcode application, enable coverage in its existing test scheme and use that build's binary/profile; do not assume SwiftPM paths. See [SwiftPM's test implementation](https://github.com/swiftlang/swift-package-manager/blob/main/Sources/Commands/SwiftTestCommand.swift) and [LLVM export options](https://llvm.org/docs/CommandGuide/llvm-cov.html#llvm-cov-export).

## Ruby and PHP: small additions to familiar runners

- **Ruby:** add SimpleCov and an LCOV/Cobertura formatter to the test dependency group. Start SimpleCov at the top of the test helper, before loading application code, and use `track_files` for production files never loaded by tests. Run the existing `bundle exec rspec` or Minitest/Rake command. See [SimpleCov setup](https://github.com/simplecov-ruby/simplecov) and Codecov's formatter recommendations above.
- **PHP:** with PHPUnit and Xdebug's coverage mode available to CLI PHP, run `XDEBUG_MODE=coverage vendor/bin/phpunit --coverage-filter src --coverage-clover coverage.xml`. Prefer the existing PHPUnit source configuration over that sample filter. PCOV is also suitable for line coverage; branch/path coverage requires Xdebug. See [PHPUnit coverage setup](https://docs.phpunit.de/en/12.4/code-coverage.html).

## Turn the first report into the badge

Follow [reporting.md](reporting.md), setting the uploader's explicit report path to the generated file listed above and verify the expected files in the processed report. For multiple languages, inspect each component before combining reports; do not average percentages. Use separate component badges when their metrics or scopes differ.
