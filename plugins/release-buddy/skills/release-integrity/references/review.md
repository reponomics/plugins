# Reviewing release integrity

Review the requested public GitHub source-release path and optional primary artifact. Report evidence-based findings at the requested depth; do not apply fixes during a review. Include versioning only for a broad process review, sharing facts and avoiding duplicate discovery. Inaccessible settings remain unverified.

## What to inspect

- **Source authorization:** the release's signed tag, expected signer trust, signed name, intended commit and matching version/notes. Check who can change tags and the signer allowlist.
- **Publication authority:** actual triggers, credentials, branch and environment policies. Trace candidate code, event inputs and downloaded artifacts into jobs with write or signing authority. A check inside untrusted candidate code cannot protect that code's execution.
- **Release identity:** immutable-release setting, draft-before-publication order, and preservation of the original tag object. Distinguish existing releases from future releases covered by a setting change.
- **Optional artifact:** build and tests from the intended source, actual provenance from the build run, original bytes carried through upload, and verification of digest and expected workflow/ref. Do not infer that release membership proves a build.
- **Consumer instructions and recovery:** authenticated key acquisition, usable verification commands, applicable version range, and a plan for a partial draft or a bad published release.

Use existing checks and read-only settings inspection where available. A review does not authorize installing scanners or conducting an unrelated CI audit. Treat existing dependency reports as scoped supporting evidence, not a reason to claim that the release is safe.

## Report

Lead with the practical conclusion and the strongest findings; include real strengths, affected files or settings, the behavior at risk, and the direction of a fix. Normally report up to five actionable findings; a requested thorough review may include more. Explain actual validation and what remains untested. Prioritize an exploitable path to publication ahead of a verification gap, and that gap ahead of optional documentation improvements. Do not promote a missing optional mechanism into a blocker.

## Badges and Scorecard

Consult the current [program definitions](sources.md#programs-that-assess-release-signing) for a requested assessment; they measure different evidence.

- OpenSSF Best Practices Silver `signed_releases` requires signatures for widely distributed results, documented public-key acquisition and verification, and private-key custody away from distribution sites. `version_tags_signed` separately suggests signing important tags. Signed source tags can provide relevant evidence for source releases, but do not cover a separately built binary just because it derives from that source. Explain the actual evidence without promising a badge outcome.
- OpenSSF Scorecard's Signed-Releases check examines GitHub release assets using recognized signature/provenance filenames and does not verify those signatures. Its current documentation excludes automatically generated source-only releases. A valid signed Git tag or GitHub release attestation alone must not be equated with that check passing. Inspect the version in use before predicting behavior.
- OSPS Baseline has its own release and verification requirements. Map only the requested controls against their current definitions; do not equate a scanner result with the Best Practices badge.

If an actual artifact already has a valid provenance bundle, uploading that genuine bundle with a recognized extension may make evidence visible to Scorecard. Do not fabricate an attestation or add an unused artifact solely for a score. When installed, `badge-buddy:ossf-bp-badges` and `badge-buddy:ossf-scorecard` handle the respective assessment tasks.
