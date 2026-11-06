# Static analysis beyond Python and JavaScript

Read the recipe for the project's language. Select one tool, run it locally, and use the same command in CI.

Static analysis reads code without exercising the application as a test would. Some tools check style and common mistakes; others concentrate on security problems. Name the badge after the check, such as `Clippy`, `Staticcheck`, or `PHPStan`. Use `Security checks` when the selected rules and enforced policy actually cover security findings. See [badge setup and baseline guidance](baseline-and-gates.md#publish-a-meaningful-badge).

See the [analyzer license table](licenses.md) for license names and OSI approval status. It also distinguishes CodeQL and Snyk's open source components from their analysis products.

## Go: vet, then Staticcheck

With Go installed, run these from the directory containing `go.mod`:

```sh
go vet ./...
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...
```

`go vet` is built in and catches suspicious constructs such as mismatched formatting arguments. Staticcheck adds a broader collection of bug, simplification, and performance checks. The installation places its executable in `GOBIN`, or `$(go env GOPATH)/bin` by default; add that directory to `PATH` if the command is not found. `./...` covers packages below the current module; repeat for separate modules in a monorepo. Use the same build tags and target platform as the supported build. [Go vet](https://pkg.go.dev/cmd/vet), [Staticcheck setup](https://staticcheck.dev/docs/getting-started/)

Use `@latest` to try Staticcheck locally, then replace it with the verified version you tested when saving CI setup. Match its supported Go versions to the project's toolchain. A `Go analysis` badge can cover both commands. For a dedicated security scan, consider [CodeQL](codeql.md); dependency vulnerability checking is a separate task.

## Rust: Clippy

For a Cargo project with a rustup-managed toolchain:

```sh
rustup component add clippy
cargo clippy --workspace --all-targets
```

Clippy explains suspicious or unnecessarily complicated Rust and suggests improvements. `--all-targets` includes tests and examples; it does not mean every operating system or every feature combination. Start with the project's normal features. Add `--all-features` only when they can all be enabled together; otherwise analyze the supported combinations separately. [Clippy usage](https://doc.rust-lang.org/clippy/usage.html), [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html)

Once the initial warnings are addressed or narrowly justified, make the badge enforce the check:

```sh
cargo clippy --workspace --all-targets -- -D warnings
```

Use the same Rust toolchain locally and in CI so new lint rules arrive through deliberate toolchain updates. Start with Clippy's default rules; enabling every pedantic rule is unnecessary for a useful first badge. For security-focused scanning, see the current Rust support and build mode in [CodeQL setup](codeql.md).

## Java and Kotlin: follow the build system

For Java, SpotBugs examines compiled classes for likely defects. In a Maven project, configure `com.github.spotbugs:spotbugs-maven-plugin` with a verified compatible version in `pom.xml`, then use the project's Maven wrapper:

```sh
./mvnw compile spotbugs:check
```

Use `mvn` if the project has no wrapper and Maven is installed. The `check` goal fails on findings; `spotbugs:spotbugs` generates analysis for an initial review. Build the intended modules first and inspect the report rather than treating missing class files as a clean scan. Add Find Security Bugs to SpotBugs when Java security patterns are the goal, following its plugin configuration. [SpotBugs Maven setup and security extension](https://spotbugs.readthedocs.io/en/stable/maven.html)

For Kotlin, detekt is the more natural source-analysis starting point. Add its Gradle plugin using the stable documentation matching your Kotlin/Gradle versions, then run:

```sh
./gradlew detekt
```

Review the generated HTML report under `build/reports/detekt/`. For JVM projects, type-aware tasks such as `detektMain` can add checks that need dependency information. Android and multiplatform builds need the appropriate module/variant tasks. Do not copy a prerelease plugin configuration just because it appears on the documentation landing page. [detekt stable Gradle guide](https://detekt.dev/docs/1.23.8/gettingstarted/gradle/)

Use `SpotBugs` or `detekt` as the badge label. For GitHub security scanning of Java/Kotlin, [CodeQL](codeql.md) is another practical choice; Kotlin extraction requires a build.

## C#/.NET: enable the SDK's analyzers

Modern .NET SDKs include analyzers that report correctness, reliability, and selected security issues during builds. In an SDK-style project, set these properties in the project file or a shared `Directory.Build.props`:

```xml
<PropertyGroup>
  <EnableNETAnalyzers>true</EnableNETAnalyzers>
  <AnalysisMode>Recommended</AnalysisMode>
</PropertyGroup>
```

Run `dotnet build` with the project's SDK and inspect the `CA` rule messages. Use `.editorconfig` for explicit rule severities. After reviewing the baseline, `dotnet build -warnaserror` turns warnings into a failing CI check; this also covers other build warnings, so selected rule severities may be a gentler first gate. Keep the SDK version consistent through the project's `global.json`. [Microsoft analyzer guidance](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview)

Label this badge `.NET analysis`. A separate [CodeQL](codeql.md) badge can show security scanning; ordinary compiler warnings alone are not equivalent to enabling analyzers.

## C and C++: give the analyzer the build context

Clang-Tidy needs the compiler flags and include paths that make your source understandable. For a CMake project, install Clang-Tidy and Ninja alongside the normal compiler and dependencies, then create a compilation database:

```sh
cmake -S . -B build-analysis -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build-analysis
clang-tidy -p build-analysis src/example.cpp
```

Replace `src/example.cpp` with a real source file. The database, `build-analysis/compile_commands.json`, records how each file is compiled. Start with a small useful ruleset in `.clang-tidy`; review diagnostics, then use the supplied `run-clang-tidy` helper to analyze the database's files in CI. Check the helper's installed name and options. Its warnings need explicit enforcement, such as `-warnings-as-errors='*'`, before the badge can mean all selected warnings passed. [Clang-Tidy documentation](https://clang.llvm.org/extra/clang-tidy/)

Cppcheck is an alternative for finding dangerous constructs and undefined behavior:

```sh
cppcheck --project=build-analysis/compile_commands.json --enable=warning,performance --error-exitcode=1
```

Install Cppcheck first; inspect missing includes and configuration errors. Embedded projects especially need correct defines and platform settings. Start with either analyzer, then add the other if useful. [Cppcheck manual](https://cppcheck.sourceforge.io/manual.html)

## Swift: SwiftLint for conventions, CodeQL for security

Install SwiftLint following its supported installation instructions, use the project's Swift/Xcode toolchain, and run `swiftlint lint` from the repository root. Review the default rules before adding opt-in rules. After cleanup, `swiftlint lint --strict` fails on warnings and makes a straightforward `SwiftLint` badge. Commit `.swiftlint.yml` so contributors and CI use the same scope and rules. SwiftLint primarily checks conventions and code quality; its badge should say that. [SwiftLint setup and configuration](https://github.com/realm/SwiftLint)

For a security-analysis badge, [CodeQL](codeql.md) supports Swift with build extraction on an appropriate macOS runner. Use the project's actual Xcode scheme or Swift package build and inspect which source files were extracted.

## Ruby and PHP: two more approachable options

| Project | First useful command | Setup and badge meaning |
| --- | --- | --- |
| Ruby on Rails | `bundle exec brakeman` | Add `brakeman` to the development dependencies and install with Bundler. A `Brakeman` badge represents Rails security scanning; this tool is not a general scanner for every Ruby library. [Quickstart](https://brakemanscanner.org/docs/quickstart/) |
| PHP | `vendor/bin/phpstan analyse src tests` | Install with `composer require --dev phpstan/phpstan`, use actual source paths, and commit the configuration and lockfile. Start at a manageable rule level and raise it gradually. `PHPStan` communicates type/correctness analysis, not a dedicated security scan. [Getting started](https://phpstan.org/user-guide/getting-started) |

Save the selected configuration, run it on pushes and pull requests, and add the [linked workflow badge](baseline-and-gates.md#publish-a-meaningful-badge).
