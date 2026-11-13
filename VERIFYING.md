# Verifying a plugin release

Current releases use a lightweight Git tag and GitHub's immutable release attestation. The publication workflow checks the exact source commit, waits for owner approval in the `release` environment, then publishes and verifies the release. Consumers verify the repository, release tag, source commit, and attached evidence against that attestation.

Marketplace installation does not automatically pin a plugin to a verified release or perform these checks. Use the verified Git tree below when inspecting or installing the particular release you intend to trust.

## Fetch the exact source

Set the official release repository and exact plugin tag you intend to use:

```sh
repo=reponomics/plugins
tag=PLUGIN--vVERSION
git clone --no-checkout --no-tags "https://github.com/$repo.git" plugin-source
cd plugin-source
git fetch --no-tags origin "refs/tags/$tag:refs/tags/$tag"
git cat-file -t "refs/tags/$tag"
git rev-parse "refs/tags/$tag"
git rev-parse "refs/tags/$tag^{commit}"
```

For current lightweight tags, the object type is `commit`, and both object IDs are the same commit SHA. Record that SHA. A lightweight tag has no personal SSH signature; its release identity is verified through GitHub's attestation below. If the object type is `tag`, follow [Historical SSH-signed tags](#historical-ssh-signed-tags) before continuing. Those annotated tags have a separate tag object ID and commit ID.

## Verify the release and its evidence

Use a GitHub CLI that supports [release verification](https://cli.github.com/manual/gh_release_verify). From a fresh download directory, with the same `repo` and `tag` values, run:

```sh
gh release verify "$tag" --repo "$repo" --format json
gh release download "$tag" --repo "$repo" --pattern osv-results.json --pattern scan-scope.md
gh release verify-asset "$tag" osv-results.json --repo "$repo"
gh release verify-asset "$tag" scan-scope.md --repo "$repo"
```

In the JSON result, find the release's Git subject under `verificationResult.statement.subject`. Require its repository and tag to match the requested release, and its `digest.sha1` to match the fetched Git ref's object ID. For current lightweight tags, this digest is the **commit SHA** itself. For historical annotated tags, it is the **tag object ID**; the verified SSH signature binds that object to the commit.

The first command checks GitHub's immutable release attestation; each [verify-asset](https://cli.github.com/manual/gh_release_verify-asset) command checks the downloaded bytes. Asset verification does not apply to GitHub's automatically generated source archives. Check that `scan-scope.md` names the same commit and read its tooling, platform, dependency inputs, and outcome alongside the JSON report.

After verification, return to the source checkout and select the verified tree:

```sh
git switch --detach "refs/tags/$tag^{commit}"
```

Check `plugins/PLUGIN/.claude-plugin/plugin.json` for the expected version and read `docs/release-notes/PLUGIN/VERSION.md` from that tree. GitHub permits editing displayed release notes after publication, so the reviewed notes in Git are the source record.

Matching the attached files proves which reports GitHub recorded for the release. It does not prove that the code, plugin guidance, generated workflows, or all downstream dependencies are free of vulnerabilities. If verification fails, keep the tag, object IDs, and error, and contact the maintainer through a known channel before using that copy.

## Historical SSH-signed tags

The previous release process used annotated SSH-signed tags. These instructions apply to those existing tags, not to all versions above a particular number: plugins version independently, and current releases use the GitHub-native process described above. Enabling immutability does not protect older releases retroactively; a historical signature alone does not establish that its GitHub release is immutable.

### Get the expected signer independently

The historical release signer is [hesreallyhim](https://github.com/hesreallyhim). Its public key is listed in [that account's SSH signing keys](https://api.github.com/users/hesreallyhim/ssh_signing_keys) with fingerprint `SHA256:IVsf0Jed2MXKHQkW/FcYtahE6OiovA5+50GxsrZPs9E`. Authenticate the account through a channel you already trust and confirm that the key was authorized for the particular plugin and version. This page alone does not establish trust in the key; a replacement requires an authenticated maintainer announcement.

Obtain the release-signing public key and expected complete SHA256 fingerprint independently of the candidate release, through direct contact with a known maintainer or a previously authenticated project announcement. A key inside the candidate tag, a key comment, or a “Verified” badge alone does not establish that authority.

Save the public key as `release-signing.pub` outside the source checkout and compare this output with the independently obtained fingerprint, character for character:

```sh
ssh-keygen -lf release-signing.pub -E sha256
```

If it matches, create a local verification file. Its first field is your local label for the trusted release signer:

```sh
{ printf 'release-maintainer namespaces="git" '; cat release-signing.pub; } > allowed_signers
signers="$PWD/allowed_signers"
```

If fingerprints disagree, the key changes without an authenticated notice, or you cannot establish authority for this release, obtain the correct key and applicable versions before continuing.

### Verify the annotated tag

Use Git with SSH signature support and OpenSSH with `ssh-keygen -Y` support. In the source checkout fetched above, with `signers` set to the absolute path of your trusted verification file, run:

```sh
git cat-file -p "refs/tags/$tag"
git -c gpg.openpgp.program=false -c gpg.x509.program=false -c gpg.ssh.allowedSignersFile="$signers" verify-tag "refs/tags/$tag"
```

Require an object of type `tag`; a signed header saying `type commit` and `tag` followed by the exact requested tag name; and successful verification with a **Good "git" signature** for your allowed principal and expected SSH key fingerprint. Checking the signed name prevents a valid signed tag from being relabeled as another historical release. A signed commit alone does not satisfy this historical tag-signature check.

Record both the tag object ID and its peeled commit ID, then [verify the release and evidence](#verify-the-release-and-its-evidence). For an annotated tag, the attested Git digest must match the tag object ID, not the peeled commit.
