# Static-analysis tool licenses and OSI status

Use these tables when selecting an analyzer or checking license preferences. **OSI approves licenses, not tools or badges**; “Yes” means the listed tool's license is on the [OSI approved-license list](https://opensource.org/licenses). Free use for open source projects is a separate question.

Checked against upstream licensing sources and OSI's list on **2026-10-31**. These are the main tool/component licenses; bundled dependencies and separately installed extensions can have their own licenses. Recheck the selected release when updating a tool.

## Local analyzers

| Tool | License / SPDX identifier | OSI-approved? | Upstream licensing source and practical note |
| --- | --- | --- | --- |
| Bandit | `Apache-2.0` | Yes | [License](https://github.com/PyCQA/bandit/blob/main/LICENSE). Python security analysis. |
| Go `vet` | `BSD-3-Clause` | Yes | [Go license](https://github.com/golang/go/blob/master/LICENSE). Included with Go. |
| Staticcheck | `MIT` | Yes | [License](https://github.com/dominikh/go-tools/blob/master/LICENSE). Additional Go checks. |
| Rust Clippy | `MIT OR Apache-2.0` | Yes, both alternatives | [License declaration](https://github.com/rust-lang/rust-clippy#license). Choose either license under the upstream terms. |
| SpotBugs | `LGPL-2.1-or-later` | Yes | [License](https://github.com/spotbugs/spotbugs/blob/master/LICENSE) and [source notice](https://github.com/spotbugs/spotbugs/blob/master/spotbugs/src/main/java/edu/umd/cs/findbugs/BugInstance.java). Java bytecode analysis. |
| Find Security Bugs | `LGPL-3.0-or-later` | Yes | [License](https://github.com/find-sec-bugs/find-sec-bugs/blob/master/LICENSE) and [license header](https://github.com/find-sec-bugs/find-sec-bugs/blob/master/LGPL-3.0-header.txt). Security extension for SpotBugs. |
| detekt | `Apache-2.0` | Yes | [License](https://github.com/detekt/detekt/blob/main/LICENSE). Kotlin analysis. |
| .NET SDK / Roslyn analyzers | `MIT` | Yes | [SDK license](https://github.com/dotnet/sdk/blob/main/LICENSE.TXT), [Roslyn license](https://github.com/dotnet/roslyn/blob/main/License.txt), and [analyzers license](https://github.com/dotnet/roslyn-analyzers/blob/main/License.txt). This entry covers the SDK/compiler/analyzer projects, not Visual Studio's product license. |
| Clang-Tidy | `Apache-2.0 WITH LLVM-exception` | Apache-2.0 is approved; the exception is listed separately here | [LLVM tools license](https://github.com/llvm/llvm-project/blob/main/clang-tools-extra/LICENSE.TXT). The LLVM exception adds permissions; do not describe it as a separate OSI-approved license. |
| Cppcheck | `GPL-3.0-or-later` | Yes | [License](https://github.com/danmar/cppcheck/blob/main/COPYING) and [source notice](https://github.com/danmar/cppcheck/blob/main/lib/cppcheck.cpp). This entry covers the community analyzer. |
| SwiftLint | `MIT` | Yes | [License](https://github.com/realm/SwiftLint/blob/main/LICENSE). Swift conventions and quality checks. |
| Brakeman | Brakeman Public Use License | **No** | [License](https://github.com/presidentbeef/brakeman/blob/main/LICENSE.md) and [distribution notice](https://github.com/presidentbeef/brakeman/blob/main/COPYING.md). Source is available, but the current distribution has commercial-use restrictions. Analyzing your own software is explicitly listed as a permitted non-commercial use under these terms. |
| PHPStan | `MIT` | Yes | [License](https://github.com/phpstan/phpstan/blob/2.1.x/LICENSE). This entry covers the open source analyzer, not PHPStan Pro. |

For the approved entries above, OSI lists [MIT](https://opensource.org/license/mit), [Apache 2.0](https://opensource.org/license/apache-2-0), [BSD 3-Clause](https://opensource.org/license/bsd-3-clause), [LGPL 2.1](https://opensource.org/license/lgpl-2-1), [LGPL 3.0](https://opensource.org/license/lgpl-3-0), and [GPL 3.0](https://opensource.org/license/gpl-3-0). `OR` offers alternative licenses; `-or-later` allows later versions under the upstream grant.

Brakeman deserves special attention when selecting only OSI-licensed tools: its retained `MIT-LICENSE` file covers older code, while its distribution notice puts the current package under the Brakeman Public Use License. A visible MIT file alone is insufficient to classify the current scanner as MIT-licensed.

## CodeQL and Snyk: distinguish the parts

| Component | License / terms | OSI-approved? | What the distinction means |
| --- | --- | --- | --- |
| CodeQL CLI / analysis engine | GitHub CodeQL Terms and Conditions | **No** | [CLI terms](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md). GitHub grants specified uses, including analysis of OSI-licensed codebases and automated analysis for those hosted and maintained on GitHub.com. This is a proprietary tool with OSS-use permissions. |
| CodeQL query libraries | `MIT` | Yes | [Query repository license](https://github.com/github/codeql/blob/main/LICENSE). The query license does not relicense the CLI. |
| CodeQL GitHub Action | `MIT` | Yes | [Action license](https://github.com/github/codeql-action/blob/main/LICENSE). The workflow integration uses the separately licensed CLI. |
| Snyk CLI | `Apache-2.0` | Yes | [CLI license](https://github.com/snyk/cli/blob/main/LICENSE). The open source client connects to services with separate terms. |
| Snyk Code / Snyk Open Source hosted services | Proprietary service terms | **No OSI software license for the hosted service** | [Snyk terms](https://snyk.io/policies/terms-of-service/). The terms also cover free plans and OSS programs; “Snyk Open Source” names the dependency-analysis product. |

For an OSI-licensed analysis toolchain, select suitable local analyzers from the first table. Hosted service terms remain separate from an open source uploader or Action.
