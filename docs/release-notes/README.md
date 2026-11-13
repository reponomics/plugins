# Writing plugin release notes

For each plugin version selected for release, add a reviewed Markdown file at `docs/release-notes/<plugin-name>/<version>.md` in the same PR as the manifest change. For example, a hypothetical Release Buddy 1.2.0 would use `docs/release-notes/release-buddy/1.2.0.md`. Use the version exactly as written in the plugin manifest, including prerelease suffixes. Each plugin gets its own file, even if several ship from the same commit.

Write for a maintainer deciding whether and how to upgrade. Lead with the user-visible change; call out breaking behavior, required action or migration steps, and relevant compatibility or security fixes. Include important changes in shared files when they affect the plugin. For an initial public release, describe what is available and its limits. Omit empty sections. Do not use raw commit subjects as a substitute for review, predict a clean vulnerability scan, or disclose a confidential issue before coordinated publication.

The release workflow reads these notes from the exact checked commit and uses them for the GitHub release body. Keep the copy in Git as the historical record; displayed GitHub release notes can be edited after publication. See [Plugin releases](../releases.md) for review, evidence, and publication, and [verification](../../VERIFYING.md) to authenticate that source.
