<!--
Consumer guide for public GitHub source releases signed with SSH and published immutably. Replace all {{PLACEHOLDER}} values, remove the optional scan and built-file sections if unused, and test commands against a real release before claiming coverage. Identify the first covered version explicitly.
-->

# Verifying {{PROJECT}} releases

These checks apply from {{FIRST_COVERED_VERSION}} onward. Earlier versions {{EARLIER_RELEASE_COVERAGE}}. The official repository is {{OWNER}}/{{REPO}}. A valid signature identifies an authorized signer and source; it does not show that the source is free of defects.

## Authenticate the release key

Obtain {{PUBLIC_KEY_LOCATION}} and confirm its complete SHA256 fingerprint through {{INDEPENDENT_TRUST_CHANNEL}}. Confirm that the signer is authorized for this release. A key supplied only by the candidate release or a “Verified” badge is insufficient. Save the authenticated public key as `release-signing.pub` outside the source checkout.

```sh
ssh-keygen -lf release-signing.pub -E sha256
{ printf 'release-maintainer namespaces="git" '; cat release-signing.pub; } > allowed_signers
signers="$PWD/allowed_signers"
```

Stop if the fingerprint differs from the independently authenticated value. Do not silently trust a replacement key.

## Verify the source tag

Set the exact release tag, including the project's prefix. These commands require Git's SSH-signature support and OpenSSH verification support. Use a fresh directory.

```sh
repo='{{OWNER}}/{{REPO}}'
tag='{{EXACT_RELEASE_TAG}}'
git clone --no-checkout --no-tags "https://github.com/$repo.git" verified-source
cd verified-source
git fetch --no-tags origin "refs/tags/$tag:refs/tags/$tag"
git cat-file -t "refs/tags/$tag"
git cat-file -p "refs/tags/$tag"
git -c gpg.openpgp.program=false -c gpg.x509.program=false -c gpg.ssh.allowedSignersFile="$signers" verify-tag "refs/tags/$tag"
```

Require an object of type `tag`, a signed header with `type commit` and the exact requested tag name, and successful verification with the expected SSH key fingerprint and allowed principal. These checks reject lightweight tags, relabeled tag objects and unauthorized signatures. See [Git's verification command](https://git-scm.com/docs/git-verify-tag).

Record the tag object and commit separately, then use the verified source:

```sh
git rev-parse "refs/tags/$tag"
commit="$(git rev-parse "refs/tags/$tag^{commit}")"
git switch --detach "$commit"
```

Check {{VERSION_PATH}} and {{SIGNED_NOTES_PATH}} for the intended version and changes. A version label alone does not establish installed-byte identity; inspect the host's install and update rules and the exact source it uses.

## Verify the immutable release

Keep the `repo`, `tag` and `commit` values above:

```sh
gh release verify "$tag" --repo "$repo" --format json
```

Require the verified release record to identify the same source commit. [Release verification](https://cli.github.com/manual/gh_release_verify) checks GitHub's attestation and works for source releases without attachments.

## Optional dependency scan files

Delete this section if no scan reports were attached. From a fresh download directory:

```sh
gh release download "$tag" --repo "$repo" --pattern osv-results.json --pattern scan-scope.md
gh release verify-asset "$tag" osv-results.json --repo "$repo"
gh release verify-asset "$tag" scan-scope.md --repo "$repo"
```

[Asset verification](https://cli.github.com/manual/gh_release_verify-asset) checks your downloaded bytes. Automatically generated source archives are not covered by asset verification.

Read the scan scope and result together. Expect {{DEPENDENCY_INPUTS_AND_PLATFORMS}} at the identified commit and time. The report covers known advisories in that inventory, not all possible vulnerabilities or downstream dependencies. Matching the release proves which report was attached.

## Optional built-file provenance

Delete this section unless {{ARTIFACT_NAME}} has GitHub build provenance from {{SIGNER_WORKFLOW}}. Download it into the fresh directory:

```sh
artifact='{{ARTIFACT_NAME}}'
gh release download "$tag" --repo "$repo" --pattern "$artifact"
gh release verify-asset "$tag" "$artifact" --repo "$repo"
gh attestation verify "$artifact" --repo "$repo" --signer-workflow '{{SIGNER_OWNER}}/{{SIGNER_REPO}}/{{WORKFLOW_PATH}}' --source-ref "refs/tags/$tag" --source-digest "$commit" --predicate-type https://slsa.dev/provenance/v1
```

Require both checks to succeed. The first binds the file to the release; the second checks build provenance, including its exact source commit and ref. For reusable workflows, the signer is the reusable workflow. Consult the [current verification manual](https://cli.github.com/manual/gh_attestation_verify) and adapt only to the project's tested build identity; do not drop failed identity checks.

If any required check fails, do not use that copy. Keep the tag, object IDs and error and contact {{MAINTAINER_CONTACT}} through a known channel.
