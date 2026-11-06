# Upstream sources

Use the owning documentation before supplying exact commands, action inputs, current defaults or platform behavior. This is a lookup map, not a claim that every page was freshly checked. If a source cannot be retrieved, mark the dependent detail unresolved. The supported implementation is public GitHub source releases with an optional primary built artifact.

## Source signing

- Git [tag objects and signing](https://git-scm.com/docs/git-tag), [tag verification](https://git-scm.com/docs/git-verify-tag), and [signature configuration](https://git-scm.com/docs/git-config).
- OpenSSH [ssh-keygen](https://man.openbsd.org/ssh-keygen): public-key fingerprints, signatures and allowed-signers format.
- GitHub [commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification): accepted formats, display and account setup. GitHub's display does not independently establish a release signer's authority.

## Release operations

- GitHub [workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow): event suppression and approval-required PR exceptions. Read the complete section, not just its opening rule.
- GitHub [release events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#release): draft event restrictions.
- GitHub [immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases), [enabling immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes), and [managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
- GitHub CLI [release creation](https://cli.github.com/manual/gh_release_create), [upload](https://cli.github.com/manual/gh_release_upload), [download](https://cli.github.com/manual/gh_release_download), [release verification](https://cli.github.com/manual/gh_release_verify), and [asset verification](https://cli.github.com/manual/gh_release_verify-asset).
- GitHub [Apps in Actions](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow): use only if that credential arrangement is selected.
- OpenSSF [vulnerability disclosure guide](https://github.com/ossf/oss-vulnerability-guide): incident coordination and recovery.

## Build provenance and verification

- GitHub [artifact attestation concepts](https://docs.github.com/en/actions/concepts/security/artifact-attestations), [implementation](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations), and [stronger build isolation](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating).
- [actions/attest](https://github.com/actions/attest): current action inputs, outputs and job permissions; resolve release SHA pins from the owning repository.
- GitHub CLI [attestation verification](https://cli.github.com/manual/gh_attestation_verify): digest, repository, signer workflow and source restrictions.
- [SLSA specification](https://slsa.dev/spec/), [in-toto statements](https://github.com/in-toto/attestation/tree/main/spec), and [Sigstore concepts](https://docs.sigstore.dev/about/overview/): claims and their limits, not automatic certification.
- [OSV-Scanner documentation](https://google.github.io/osv-scanner/): supported inputs, pinned scanner setup and interpretation of a deliberately selected dependency report.

## Reviewing a release setup

- GitHub [secure use of Actions](https://docs.github.com/en/actions/reference/security/secure-use): untrusted code, inputs and credentials.
- GitHub [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) and [environment protections](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

## Programs that assess release signing

- [OpenSSF Best Practices Silver](https://www.bestpractices.dev/en/criteria/1): `signed_releases` and `version_tags_signed`.
- [OpenSSF Scorecard Signed-Releases](https://github.com/ossf/scorecard/blob/main/docs/checks.md#signed-releases): recognized asset evidence and limitations. Check the implemented tool version when assessing a result.
- [OSPS Baseline](https://baseline.openssf.org/): independently defined release and verification controls.

## Versioning and other channels

Versioning tool sources remain in [release-versioning](../../release-versioning/references/sources.md). Registry publishing and container distribution need their own upstream documentation and implementation expertise; this plugin's source-release instructions do not implement those channels.

For an out-of-scope request, start with the provider’s own guide: [npm trusted publishing](https://docs.npmjs.com/trusted-publishers/), [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/), or [GitHub container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry). These links are handoffs, not additional supported setup paths.
