# Coverage tool licenses

Use this table when selecting coverage tools or checking license preferences. OSI approves **licenses**, not individual tools, hosted services, or badges. The links below identify the upstream license and the corresponding OSI entry; checked on **2026-10-31**. Check the license shipped with the version you install when upgrading.

| Tool | Upstream license | OSI status |
| --- | --- | --- |
| coverage.py | [Apache-2.0](https://github.com/nedbat/coveragepy/blob/master/LICENSE.txt) | [Approved](https://opensource.org/license/Apache-2.0) |
| pytest-cov | [MIT](https://github.com/pytest-dev/pytest-cov/blob/master/LICENSE) | [Approved](https://opensource.org/license/MIT) |
| Vitest | [MIT](https://github.com/vitest-dev/vitest/blob/main/LICENSE) | [Approved](https://opensource.org/license/MIT) |
| Jest | [MIT](https://github.com/jestjs/jest/blob/main/LICENSE) | [Approved](https://opensource.org/license/MIT) |
| Go's built-in coverage tools | [BSD-3-Clause](https://go.dev/LICENSE) | [Approved](https://opensource.org/license/BSD-3-Clause) |
| cargo-llvm-cov | [Apache-2.0](https://github.com/taiki-e/cargo-llvm-cov/blob/main/LICENSE-APACHE) OR [MIT](https://github.com/taiki-e/cargo-llvm-cov/blob/main/LICENSE-MIT), at your option | Both approved: [Apache-2.0](https://opensource.org/license/Apache-2.0), [MIT](https://opensource.org/license/MIT) |
| JaCoCo | [EPL-2.0](https://github.com/jacoco/jacoco/blob/master/LICENSE.md) | [Approved](https://opensource.org/license/EPL-2.0) |
| Kover | [Apache-2.0](https://github.com/Kotlin/kotlinx-kover/blob/main/LICENSE.TXT) | [Approved](https://opensource.org/license/Apache-2.0) |
| Coverlet | [MIT](https://github.com/coverlet-coverage/coverlet/blob/master/LICENSE) | [Approved](https://opensource.org/license/MIT) |
| GCC / gcov | [GPL-3.0-or-later](https://github.com/gcc-mirror/gcc/blob/master/gcc/gcov.cc) | [GPLv3 approved](https://opensource.org/license/GPL-3.0); runtime libraries have additional exceptions |
| gcovr | [BSD-3-Clause](https://github.com/gcovr/gcovr/blob/main/LICENSE.txt) | [Approved](https://opensource.org/license/BSD-3-Clause) |
| LLVM / llvm-cov | [Apache-2.0 WITH LLVM-exception](https://github.com/llvm/llvm-project/blob/main/llvm/LICENSE.TXT) | [Apache-2.0 base approved](https://opensource.org/license/Apache-2.0); exception identified separately below |
| Swift / SwiftPM | Apache-2.0 with runtime library exception ([Swift](https://www.swift.org/LICENSE.txt), [SwiftPM](https://github.com/swiftlang/swift-package-manager/blob/main/LICENSE.txt)) | [Apache-2.0 base approved](https://opensource.org/license/Apache-2.0); exception identified separately below |
| Xcode and Apple SDKs | [Apple's Xcode and SDK agreement](https://www.apple.com/legal/sla/docs/xcode.pdf) | Proprietary agreement, not OSI-approved; distinct from open source Swift/LLVM components |
| SimpleCov | [MIT](https://github.com/simplecov-ruby/simplecov/blob/main/LICENSE) | [Approved](https://opensource.org/license/MIT) |
| simplecov-cobertura, one Ruby report formatter option | [Apache-2.0](https://github.com/jessebs/simplecov-cobertura/blob/master/LICENSE) | [Approved](https://opensource.org/license/Apache-2.0) |
| PHPUnit / php-code-coverage | BSD-3-Clause ([PHPUnit](https://github.com/sebastianbergmann/phpunit/blob/main/LICENSE), [php-code-coverage](https://github.com/sebastianbergmann/php-code-coverage/blob/main/LICENSE)) | [Approved](https://opensource.org/license/BSD-3-Clause) |
| PCOV | [PHP-3.01](https://github.com/krakjoe/pcov/blob/develop/LICENSE) | [Approved](https://opensource.org/license/PHP-3.01) |
| Xdebug | [Xdebug License 1.03](https://xdebug.org/license), a modified PHP license | Not listed in the [OSI-approved license directory](https://opensource.org/licenses); PHP license approval does not automatically cover this modification |
| Codecov GitHub Action | [MIT](https://github.com/codecov/codecov-action/blob/main/LICENSE) | [Approved](https://opensource.org/license/MIT); applies to the action |
| Codecov CLI | [Apache-2.0](https://github.com/codecov/codecov-cli/blob/main/LICENSE) | [Approved](https://opensource.org/license/Apache-2.0); applies to the CLI |

The LLVM and Swift runtime exceptions grant additional permissions on top of Apache-2.0. Their SPDX identifiers are [LLVM-exception](https://spdx.org/licenses/LLVM-exception.html) and [Swift-exception](https://spdx.org/licenses/Swift-exception.html); an SPDX identifier is not itself OSI approval. GCC's [runtime library exception](https://gcc.gnu.org/onlinedocs/libstdc++/manual/license.html) is likewise separate from gcov's own license. These entries describe the named tools' main licenses, not every bundled dependency or file.

When OSI approval is a requirement, PCOV is the listed PHP option for line coverage, while the existing Xdebug recipe remains useful for branch/path coverage under its own license.

Codecov's hosted reporting and badge service has its own [service terms](https://about.codecov.io/terms-of-service-v1/). The open source licenses of its action and CLI do not describe the hosted service. You can use those tools and a hosted badge together; if you want reporting entirely under your own control, use the local reports and generated-badge path in [reporting.md](reporting.md).
