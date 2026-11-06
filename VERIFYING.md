# Verifying a plugin release

The downloadable plugin is source in Git. For releases made with the signed-tag process, verify the maintainer’s signature on the plugin tag before using its contents. Then check GitHub’s immutable release record if you need to verify the attached dependency scan. These checks answer different questions: who approved this source, and which files GitHub recorded for this release.

## Get the expected signer independently

For releases beginning with `0.3.0-beta.1`, the authorized maintainer is [hesreallyhim](https://github.com/hesreallyhim). The release-signing public key is listed in [that account's SSH signing keys](https://api.github.com/users/hesreallyhim/ssh_signing_keys) with the SHA256 fingerprint `SHA256:IVsf0Jed2MXKHQkW/FcYtahE6OiovA5+50GxsrZPs9E`. Authenticate the maintainer's account through a channel you already trust; this page alone does not establish trust in the key. A replacement key requires an authenticated maintainer announcement.

Obtain the release signing **public key** and its expected **SHA256 fingerprint** from the maintainer. Confirm the complete fingerprint through a channel you already trust independently of this release, such as direct contact with a known maintainer or a previously authenticated project announcement. Confirm that the key was authorized for this plugin and version. A key found inside the candidate tag, a comment on a key, or a “Verified” badge alone does not establish that authority.

Save the public key as `release-signing.pub` outside the source checkout. Compare the fingerprint in the following output with the independently obtained value, character for character:

```sh
ssh-keygen -lf release-signing.pub -E sha256
```

If it matches, use the key to make a one-key verification file. The first field below is your local label for this trusted release signer.

```sh
{ printf 'release-maintainer namespaces="git" '; cat release-signing.pub; } > allowed_signers
signers="$PWD/allowed_signers"
```

If fingerprints disagree, a key changes without an authenticated notice, or you cannot establish trust, stop. Obtain the correct key and applicable versions from the maintainer before continuing.

## Verify the exact source tag

Use Git with SSH signature support and OpenSSH with `ssh-keygen -Y` support. Set the repository to the official release repository you intended to use, and replace the example tag with the exact plugin name and published version.

```sh
repo=OWNER/REPOSITORY
tag=PLUGIN--vVERSION
git clone --no-checkout --no-tags "https://github.com/$repo.git" plugin-source
cd plugin-source
git fetch --no-tags origin "refs/tags/$tag:refs/tags/$tag"
git cat-file -t "refs/tags/$tag"
git cat-file -p "refs/tags/$tag"
git -c gpg.openpgp.program=false -c gpg.x509.program=false -c gpg.ssh.allowedSignersFile="$signers" verify-tag "refs/tags/$tag"
```

Require all three results: an object of type `tag`; its signed header says `type commit` and `tag` followed by the exact requested tag name; and `verify-tag` succeeds with a **Good "git" signature** for your allowed principal and the expected SSH key fingerprint. Checking the signed name prevents a valid tag from being relabeled as another release. A lightweight tag points directly to a commit. Even if that commit is signed, it does not sign the release name or authorize that version.

After verification, record the tag object ID and the commit ID. They identify different Git objects. Use that verified tree when inspecting or installing the plugin.

```sh
git rev-parse "refs/tags/$tag"
git rev-parse "refs/tags/$tag^{commit}"
git switch --detach "refs/tags/$tag^{commit}"
```

Check the version under `plugins/PLUGIN/.claude-plugin/plugin.json` and read the corresponding `docs/release-notes/PLUGIN/VERSION.md`.

## Verify the GitHub release and its evidence

Using a GitHub CLI with [release verification](https://cli.github.com/manual/gh_release_verify), run these from a fresh download directory with the same `repo` and `tag` values:

```sh
gh release verify "$tag" --repo "$repo" --format json
gh release download "$tag" --repo "$repo" --pattern osv-results.json --pattern scan-scope.md
gh release verify-asset "$tag" osv-results.json --repo "$repo"
gh release verify-asset "$tag" scan-scope.md --repo "$repo"
```

Compare the commit in the verified release record with your peeled Git commit ID. The first command checks GitHub’s release attestation; each [verify-asset](https://cli.github.com/manual/gh_release_verify-asset) command checks the downloaded bytes. This check does not apply to GitHub’s automatically generated source archives. Read the reviewed release notes from the signed Git tree: GitHub permits editing the displayed notes even after publication.

Read `scan-scope.md` alongside the JSON for the revision, tooling and dependency inputs covered. Matching those files to the release proves which report was attached. It does not prove that the code, plugin guidance, generated workflows or all downstream dependencies are free of vulnerabilities. If a required check fails, do not use that copy; keep the tag, object IDs and error, and contact the maintainer through a known channel.
