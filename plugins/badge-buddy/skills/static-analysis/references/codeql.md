# CodeQL setup and configuration

Inspect the repository's current code-scanning setting and workflows. Prefer default setup when its detected languages, build behavior, and query choices meet the need: open the repository's security settings, select CodeQL default setup, review the detected languages, enable it, and inspect the first run. Use advanced setup for explicit build commands or workflow control. When switching, disable default setup rather than running both: GitHub can reject competing CodeQL uploads. [GitHub setup documentation](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configure-code-scanning)

Code scanning is available for public GitHub.com repositories. For private repositories, GitHub documents organization-owned repositories on Team/Enterprise with GitHub Code Security enabled; check the relevant entitlement or Enterprise Server version in that case. [Availability and build support](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages)

When comparing tools, use the [component license table](licenses.md) to distinguish CodeQL's CLI terms from its query and Action licenses.

## Match the language and build

Check the [current support table](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/) for the actual language version and framework. As checked on 2026-10-31, the main Action language identifiers include `actions`, `c-cpp`, `csharp`, `go`, `java-kotlin`, `javascript-typescript`, `python`, `ruby`, `rust`, and `swift`. Do not interpret support for one language as support for every framework or generated artifact in that language.

| Source | Build choice |
| --- | --- |
| Python, Ruby, JavaScript/TypeScript, Actions | `none`; do not add an application build merely to satisfy CodeQL. |
| C/C++, C#, Java without Kotlin | `none`, `autobuild`, or `manual`; choose based on extraction accuracy and build reproducibility. |
| Rust | `none` is the supported build mode. |
| Go, Kotlin, Swift | Use supported build extraction; do not choose `none`. |

No-build analysis can miss context available through a real build, particularly generated sources or unavailable dependencies. For `manual`, initialize CodeQL, run the intended clean build, then analyze. A successful build that reused cached output may fail to expose the intended compilation to the extractor. Use a language matrix for mixed repositories and verify the extracted files/diagnostics per language. Swift needs an appropriate macOS runner. Consult the language-specific [build instructions](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages), especially for mixed Java/Kotlin projects.

## Adapt advanced setup deliberately

The [Python template](../assets/templates/workflows/codeql-python.yml) uses no build, standard queries, GitHub-hosted runners, PR scanning, and default-branch/scheduled refresh. Replace `main` with the actual branch; add supported languages only after choosing their build modes. The pinned actions were checked on 2026-10-31; recheck releases and runner requirements when installing them. Enterprise Server needs compatible versions, not a blind copy of the GitHub.com example.

Start with the standard security suite. Consider `security-extended` after reviewing useful extra coverage and noise. If a configuration file is needed, connect it explicitly with `config-file`; a file sitting in `.github/codeql/` alone changes nothing. Test path exclusions against source coverage. `paths`/`paths-ignore` in workflow triggers control execution, not extraction; analysis path filtering has language/build-mode restrictions. Prefer selection through the actual build for compiled extraction. Keep analysis categories stable and unique when analyzing separate languages or components. [Workflow configuration](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options)

Keep `security-events: write` on the analysis job, retaining `contents: read` for checkout. Add other permissions only for a demonstrated requirement, such as fetching private query packs. `analyze` already uploads results; adding `upload-sarif` for the same run duplicates that work. [Action usage and permissions](https://github.com/github/codeql-action/blob/main/README.md)

Use `pull_request` on its normal merge revision. GitHub code scanning supports uploads for PR analysis even with restricted tokens, so switching to privileged `pull_request_target` is unnecessary. Keep untrusted builds on isolated runners without unrelated credentials. [Restricted-token upload guidance](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/resource-not-accessible)

If a merge queue requires this check, include `merge_group` and verify it runs. Avoid path filters that leave required checks pending. [Workflow trigger guidance](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options)

## Verify findings and enforcement separately

Inspect the analysis summary and code-scanning tool status for the intended commit, language, files, and diagnostics. Add the [linked README badge](baseline-and-gates.md#publish-a-meaningful-badge) and review the findings with the maintainer. CodeQL's successful analysis job means the scan ran; open findings are addressed separately. When the maintainer wants to block new findings, configure the selected severity rule and verify it on a representative PR. Code-scanning rules have documented exceptions, including merge queue groups; requiring a workflow check and configuring code-scanning merge protection are distinct mechanisms. [Code-scanning merge protection](https://docs.github.com/en/code-security/concepts/code-scanning/merge-protection)
