# Baseline, triage, and enforcement

Use this guide after selecting a scanner: establish its baseline, triage findings, choose enforcement, and describe the result accurately in a badge.

## Establish an honest starting point

1. Record the commit, analyzer/CLI version, query/rule version where available, configuration, source roots, supported languages, exclusions, and service context. Keep credentials out of saved commands and reports.
2. Run the existing or selected tool against the full intended source scope. Keep the original report and operational diagnostics. Check that intended files were analyzed; investigate parse failures, missing builds, unsupported files, zero-file scans, missing output, and timeouts before counting findings.
3. Review the highest-risk findings first using the real call path, input trust, and deployment context. Classify each as a defect to fix, a justified false positive, or an explicitly accepted risk. Severity and confidence are different; an uncertain high-impact issue deserves investigation, not automatic dismissal.
4. Track findings that need more work in the project's issue tracker and note when to revisit them. Suppress the smallest applicable rule/location with a rationale, and distinguish a real issue deferred for later from a false positive. Do not exclude tests, scripts, or whole directories solely because they produce findings.
5. Preserve a comparable baseline. A change to tool version, queries, scope, or suppression policy needs a new review; do not claim a reduction in vulnerabilities merely because fewer files or rules ran.

## Introduce a gate the team can maintain

Start with an advisory period if needed: show the findings while the maintainer learns the tool, then decide which findings should block a change. Even during that period, fail on missing or invalid analysis; handle findings using the tool's documented status rather than treating every nonzero exit alike. Retain reports from failing runs so maintainers can investigate.

For legacy debt, block newly introduced actionable findings while scheduling the existing queue. If reliable changed-finding comparison is unavailable, start with a clearly stated severity/confidence threshold or a bounded component scope; do not pretend this is a new-findings-only gate. Keep the full report visible so lower-severity findings do not vanish from review. Protect baseline and exclusion edits with review. Never regenerate an accepted baseline on each PR.

Distinguish three results: the scanner executed successfully, findings were uploaded successfully, and the configured policy permitted merging. Verify each separately. Run a controlled fixture or representative PR to check expected findings and enforcement; never add a live exploitable endpoint just to test a gate. A missing secret, unsupported project, rejected upload, or skipped fork job is unavailable analysis rather than a clean result.

## Publish a meaningful badge

A static-analysis workflow badge is useful evidence of an operating check when it links to runs and names what the check establishes. For an adapted workflow named `codeql-python.yml`, replace `OWNER`, `REPO`, and `BRANCH` in this README example; URL-encode a branch containing reserved characters:

```markdown
[![CodeQL analysis](https://github.com/OWNER/REPO/actions/workflows/codeql-python.yml/badge.svg?branch=BRANCH&event=push)](https://github.com/OWNER/REPO/actions/workflows/codeql-python.yml)
```

Confirm the linked branch has executed the intended workflow successfully before describing the badge as active. State nearby that it reports analysis execution; CodeQL can successfully analyze/upload while alerts remain unresolved. A separate enforced Bandit/security gate can use a label such as `Security checks`, with its threshold and exclusions documented. Do not label either badge `vulnerability-free`. [GitHub workflow badge documentation](https://docs.github.com/en/actions/how-tos/monitor-workflows/add-a-status-badge)

This work also supports OpenSSF Best Practices evidence. Passing `static_analysis` calls for static analysis before major production releases when a FLOSS tool is available; compiler warnings and safe modes alone do not meet that criterion. `static_analysis_common_vulnerabilities` is suggested at Passing and required at Silver, `static_analysis_fixed` concerns timely fixes for confirmed medium-or-higher exploitable vulnerabilities, and `static_analysis_often` recommends frequent runs. Hand the tool, source scope, frequency, actual runs, and remediation evidence to [the badge skill](../../ossf-bp-badges/SKILL.md) to check the applicable current wording and record answers. For Scorecard, inspect the actual published result through [the Scorecard skill](../../ossf-scorecard/SKILL.md).
