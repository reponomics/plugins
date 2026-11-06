# reponomics

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/marketplace/marketplace-dark-840x240.png">
  <img alt="reponomics: Plugins to help you grow and maintain." src="docs/assets/marketplace/marketplace-light-840x240.png" width="840">
</picture>

Plugins to help open source projects grow and maintain: quickstart a repo with core community health files; expert assistance for achieving the [OpenSSF Best Practices](https://www.bestpractices.dev/) badges and meeting the standards for the [OpenSSF Scorecard](https://scorecard.dev/); and, establish release workflows with proper versioning, security, and provenance.

> [!IMPORTANT]
> These are independent community projects. They are not affiliated with or endorsed by the Open Source Security Foundation (OpenSSF), The Linux Foundation, or GitHub.

## Plugins

| Plugin             | What it does                                                                                                                                                                                                                                                                                                               | Docs                                                       |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **badge-buddy**    | Helps projects of any size achieve meaningful open source badges. An unofficial guide and implementation assistant for the OpenSSF Best Practices badges (Passing, Silver, Gold), the Security Baseline, and Scorecard. Set up useful coverage and analysis badges, improve testing, and maintain secure GitHub workflows. | [plugins/badge-buddy](plugins/badge-buddy/README.md)       |
| **starter-buddy**  | Quickstart a GitHub repository with key community-files, issue templates, and other sensible defaults, to save you time setting up any project.                                                                                                                                                                            | [plugins/starter-buddy](plugins/starter-buddy/README.md)   |
| **release-buddy**  | Versioning and changelog guidance, plus signed source tags and immutable GitHub releases with optional build provenance and scoped dependency evidence.                                                                                                                                                                    | [plugins/release-buddy](plugins/release-buddy/README.md)   |
| **badge-progress** | A mod for Badge Buddy users: a pane with each badge section's answer counts, and a progress bar above the prompt while Claude records answers.                                                                                                                                                                             | [plugins/badge-progress](plugins/badge-progress/README.md) |
| **workflow-guard** | A mod that stops Claude from adding unpinned actions or broad top-level token permissions to GitHub Actions workflows.                                                                                                                                                                                                     | [plugins/workflow-guard](plugins/workflow-guard/README.md) |

## Install

Add the marketplace once:

```sh
claude plugin marketplace add reponomics/plugins
```

Then install the plugins you want:

```sh
claude plugin install badge-buddy@reponomics
claude plugin install starter-buddy@reponomics
claude plugin install release-buddy@reponomics
claude plugin install badge-progress@reponomics
claude plugin install workflow-guard@reponomics
```

Badge Buddy’s command-line helpers require Python 3.11 or newer, available as `python3` on your PATH. Badge Progress and Workflow Guard are mods: plugins of TypeScript function hooks that change Claude Code's interface and behaviour, which need a Claude Code version with mod support.

Each plugin's README explains what to ask for once it is installed. Badge Buddy responds to "OpenSSF Best Practices", "Security Baseline", or "OpenSSF Scorecard"; Starter Buddy responds to requests to set up community files, prepare a repository for its first contributors, or review GitHub's Community Standards checklist.

## Project structure

<!-- prettier-ignore-start -->

<!-- treestamp:start -->
<!-- treestamp:config
hidden = [".github", ".gitignore", ".nvmrc", ".pre-commit-config.yaml", ".prettierignore", ".prettierrc.json", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "LICENSE", "Makefile", "SECURITY.md", "THIRD_PARTY_NOTICES.md", "package-lock.json", "package.json", "plugins/badge-buddy/.claude-plugin", "plugins/badge-buddy/THIRD_PARTY_NOTICES.md", "plugins/badge-buddy/assets", "plugins/badge-buddy/scripts", "plugins/release-buddy/.claude-plugin", "plugins/starter-buddy/.claude-plugin", "plugins/starter-buddy/scripts", "requirements-dev.txt", "ruff.toml", "upstream-review-paths.txt"]
-->
```sh
./
├── .claude-plugin/
├── docs/
├── plugins/
│   ├── badge-buddy/
│   │   ├── skills/
│   │   │   ├── coverage-baseline/
│   │   │   ├── github-workflow-maintenance/
│   │   │   ├── ossf-bp-badges/
│   │   │   ├── ossf-scorecard/
│   │   │   └── static-analysis/
│   │   └── README.md
│   ├── badge-progress/
│   ├── release-buddy/
│   │   ├── skills/
│   │   │   ├── explain/
│   │   │   ├── release-integrity/
│   │   │   └── release-versioning/
│   │   └── README.md
│   ├── starter-buddy/
│   │   ├── skills/
│   │   │   └── community-health/
│   │   └── README.md
│   └── workflow-guard/
├── tests/
├── tools/
├── README.md
└── VERIFYING.md
```

Maintained with [treestamp](https://github.com/reponomics/treestamp)
<!-- treestamp:end -->

<!-- prettier-ignore-end -->

## Development

```bash
make setup            # create the local venv
make check            # run every plugin's tests, then compile every Python source
make plugin-validate  # validate each plugin's structure (needs the Claude Code CLI)
make mod-test         # run the mods' tests (needs the Claude Code CLI)
```

The runtime uses only the Python standard library; the local `venv` holds the development dependencies. `make check` runs the plugin and maintenance suites in separate processes and compiles the Python sources. Continuous integration runs the same target on every push and pull request. See [criteria maintenance](docs/criteria-maintenance.md) for catalog updates and [plugin releases](docs/releases.md) for how to release a plugin: bump its manifest, sign the tag, review the OSV report, then publish the immutable draft. See [Verifying a plugin release](VERIFYING.md) to check a signed release and its attachments.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to file issues and propose changes.

---

The plugin code is licensed under [MIT](LICENSE). Starter Buddy's issue, pull request, and security template variants, including our adaptations, are separately dedicated under [CC0-1.0](plugins/starter-buddy/skills/community-health/LICENSE-CC0.txt). Users may copy and adapt those variants without retaining attribution or license notices.

Badge Buddy includes material from the OpenSSF Best Practices badge contributors and the OpenSSF Security Baseline and Scorecard projects. See [third-party notices](THIRD_PARTY_NOTICES.md) for attribution, sources, and licensing information.

OpenSSF® is a trademark of The Linux Foundation. "OpenSSF Best Practices" refers to the badge program operated at [bestpractices.dev](https://www.bestpractices.dev/), and "OpenSSF Scorecard" to the project at [scorecard.dev](https://scorecard.dev/); these plugins are independent tools for working with those programs.
