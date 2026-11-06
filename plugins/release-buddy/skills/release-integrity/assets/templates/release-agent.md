<!--
Project-specific agent instructions. Replace every {{PLACEHOLDER}} from the maintainer's accepted release guide and authorization; remove unused instructions. Save where the project's agents read instructions. This template creates no new authorization.
-->

# Release protocol for {{PROJECT}}

Read [RELEASING.md]({{RELEASING_PATH}}) before release work. It defines the version, signed tag, checks, draft review and final publication. Carry forward the user's existing authorization. Resolve a material contradiction or new permanent consequence before proceeding.

For preparation, inspect source and workflow runs, draft version changes and notes, run authorized checks, and verify existing releases. Signing, pushing a release tag and publishing require authorization for that release or the recorded standing policy: {{RELEASE_AUTHORIZATION}}. Do not ask again for an already approved step.

## Follow the agreed path

1. Identify the reviewed version, notes and exact source commit. Preserve the project's existing versioning policy.
2. Verify the annotated tag against independently trusted signer policy. Check the signed name, direct commit target and expected commit. Keep the private signing key with the maintainer, outside CI.
3. Run {{PREPARE_COMMAND}}. Confirm the required checks apply to that commit. If an OSV scan was selected, inspect its scope and outcome; incomplete execution of the selected scan blocks preparation, and findings follow the agreed release gate and documented exception policy. Identity mismatches always block preparation.
4. Inspect the complete draft and compare its files with the successful run's original evidence. If a primary build artifact is included, verify its exact source and workflow provenance before attachment.
5. When authorized, run {{FINALIZE_COMMAND}} to recheck and publish. Verify the immutable release and downloaded files using [VERIFYING.md]({{VERIFYING_PATH}}). Report what actually passed and any unresolved step.

Do not move or replace a release tag, overwrite unknown draft assets, introduce unapproved credentials, or bypass a failed check. Keep build and dependency-install steps out of jobs with publication authority. When scanning is part of the agreed process, an incomplete scan is not a clean scan.

When a step fails, report its error and run link. Preserve original outputs and keep a partial draft unpublished while following the guide's recovery procedure. Correct already signed release content with a new version. Do not use UI publication to bypass the agreed final checks.
