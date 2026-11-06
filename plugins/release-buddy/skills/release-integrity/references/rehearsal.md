# Rehearsing the supported release path

A rehearsal is optional and does not authorize publication. State the boundary before running it: local signing and verification can test source identity; a real GitHub run is needed to exercise hosted provenance; immutable publication consumes a tag name that cannot simply be reused.

## Source and draft

Use disposable Git repositories and test keys for signature fixtures. Verify rejection of an unsigned or wrong-key tag and a valid signed tag object presented under another name. These fixtures establish mechanics, not the identity of the project's real signer. Do not create or replace that signer as part of a test.

In the real repository, stop at a draft when publication has not been requested. Inspect its signed tag, reviewed source and notes. Use a separate scratch repository and throwaway tags if immutable publication and release verification need a live rehearsal; explain that the scratch identity differs from the production one.

## Optional artifact

Inspect the build command and hooks first. A command called a dry run can still execute scripts or contact external services. Use a disposable environment without publication credentials for local packaging checks; do not run arbitrary hooks merely because upload is disabled.

To test hosted provenance, build and attest the primary artifact in the same GitHub run, retain the exact output and verify the downloaded bytes against that run's intended identity. Leave the release as a draft unless publication is authorized. A local build does not prove hosted identity or a successful publication.

## Evidence and handoff

Record what was exercised and the remaining first-release check. If the project already provides an OSV report, state its input files, revision, environment, scanner version and time; missing coverage or an operational error is not a clean result. For an explicitly requested scan setup, follow [the scoped OSV guidance](release-operations.md#optional-osv-evidence); do not add a scanner merely to rehearse signing. Verification of a report's release membership proves which report was attached, not that every dependency or the source is free of vulnerabilities.
