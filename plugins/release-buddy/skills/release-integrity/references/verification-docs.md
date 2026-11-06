# Consumer verification instructions

Adapt [VERIFYING.md](../assets/templates/VERIFYING.md) to the actual source release and optional primary artifact. Remove inapplicable sections. Keep the result short enough to follow before using the software; link it from the README and an existing security policy.

## Source identity

State the official repository, exact tag convention and first covered version. Explain how consumers obtain the signing public key and independently authenticate its full fingerprint. The key must not derive its authority solely from the release being checked. For SSH, supply an allowed-signers example containing actual verified values; for an existing GPG setup, use its trusted fingerprint and current Git/GPG commands.

Verify the signed annotated tag, exact signed name and expected commit. Warn that a signed commit under an unsigned tag is a different guarantee. Retain the verified tag object and consume its source rather than subsequently installing an unverified moving branch. Older unsigned releases remain uncovered.

## Immutable release membership

Use GitHub's current `gh release verify` command for the release record and `gh release verify-asset` for each downloaded attached file. Check the verified Git subject's repository and tag identity, and compare its digest with the verified tag object ID. For a signed annotated tag, this is the tag object's digest, not the peeled commit ID; the verified tag binds that object to the intended source commit. Do not claim that checking the release alone checks a local file, or that GitHub's automatically generated source archives are covered as uploaded assets. A release membership check is not build provenance.

## Optional built artifact

Describe the one distributed artifact, platform and exact filename. Verify its digest and actual build provenance with the expected repository, signer workflow and source ref or commit. Copy command options from current upstream documentation; an owner/repository restriction alone does not enforce every identity field. For keyless signing, record the issuer and exact identity or an anchored pattern. Broad unanchored patterns can accept a different repository or workflow.

Show the expected success and rejection behavior. A signature proves a binding to the signer; a build attestation makes build claims for the named subject. Neither establishes that the software is safe. A publish attestation, an OSV report or an SBOM must not be described as proof of a build.

## Validate the page

Run each command against the actual release when available; otherwise identify the first release to which the page will apply and the checks still pending. Use disposable fixtures to confirm rejection of the wrong key, relabeled tag or altered artifact where relevant. Do not execute downloaded software before its verification merely to check its version.

When a workflow or key changes, update the expected identity and applicable version range together. State what to do on failure: stop using the unverified copy, check the requested version and download source, and contact the maintainer through a known channel.
