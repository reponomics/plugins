# Badge Buddy

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../../docs/assets/badge-buddy/badge-buddy-dark-840x240.png">
  <img alt="Badge Buddy: Badges that make a difference" src="../../docs/assets/badge-buddy/badge-buddy-light-840x240.png" width="840">
</picture>

Badge Buddy helps maintainers work through the [OpenSSF Best Practices](https://www.bestpractices.dev/) badge application, understand its criteria, and improve their projects. It also explains [OpenSSF Scorecard](https://scorecard.dev/) results, helps maintain GitHub Actions workflows, establishes useful test-coverage baselines, and configures static analysis.

> [!NOTE]
> Badge Buddy is an independent community project. It is not affiliated with or endorsed by the Open Source Security Foundation (OpenSSF) or The Linux Foundation.

## Get started

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) so `uvx` is available to your host, and use Python 3.11 or newer. The plugin registers the published `best-practices-mcp==0.5.0` stdio server for BadgeApp operations. The separate Scorecard helper and local board renderer use Python’s standard library.

Add the marketplace and install the plugin in Claude Code:

```sh
claude plugin marketplace add reponomics/plugins
claude plugin install badge-buddy@reponomics
```

Ask for the help you need:

- “Help me fill out the OpenSSF Best Practices application.”
- “What does this Silver criterion mean for my project?”
- “Show me my current answers.”
- “Help me implement this missing practice.”

Badge Buddy covers Passing, Silver, Gold, and Security Baseline levels 1–3. You can ask questions, prepare answers, or work on the project as the conversation develops. For a new application, [register your project](https://www.bestpractices.dev/projects/new) on the badge website. Registration is not needed for explanations or implementation help, and you can ask to prepare answers before registering.

Reload the plugin or restart the host after installation, then check that its `bestpractices` MCP server is connected. The server runs `uvx --from best-practices-mcp==0.5.0 bestpractices-mcp`; it requires no BadgeApp credentials. Other MCP hosts can register that command manually if they do not load plugin MCP configuration. Tool prefixes vary by host. If connection fails, restore the MCP connection before application operations rather than falling back to the retired BadgeApp CLI.

## Preparing answers

The application is yours, and you decide what to record and submit. The badge is self-reported, and Claude works with you in good faith: it takes your account of your project at your word, including things it cannot independently verify. It uses the official criterion text, the repository, and what you tell it to help draft answers and supply any required links or explanations. If something appears inconsistent with the facts or a criterion, it assumes clarification is needed, explains the discrepancy, and helps you work through it, allowing for context it may have missed.

A second agent reviews Claude's work before Claude presents its drafted answers or revisions to you. It checks whether Claude understood the criteria, wrote clearly, represented your account faithfully, and respected your instructions and control of the form. Your answers provide context for that review; the reviewer has no role in approving your application or vetting your honesty. You can skip the review or stop at any time. See the [peer review instructions](skills/ossf-bp-badges/references/peer-review.md).

For the Metal badges, a response and its effect on badge progress are distinct:

- Applicable `MUST` and `MUST NOT` requirements must be satisfied.
- An absent `SHOULD` practice is `Unmet`. It can still count toward the badge when accompanied by an adequate rationale.
- An absent `SUGGESTED` practice is also `Unmet`; answering it satisfies the badge's requirement to consider the practice.

`Met` means the practice is implemented. Unknown answers remain `?`, and `N/A` follows the criterion's applicability rules. You can save and submit an application with work still to do.

## Saving and reviewing progress

Claude can keep a caller-owned JSON draft and pass it explicitly to the MCP, or use its optional server-managed draft storage. Explicit documents are the normal workflow and need no server storage. Existing repository files and your established storage preference take precedence. Old plugin assessments remain readable JSON; see [migration guidance](skills/ossf-bp-badges/references/application.md#existing-plugin-drafts) before reusing them. No files are moved automatically.

If you keep `.bestpractices.json` in your repository, Claude normally prepares changes in a temporary copy. You review those changes before they are written back, and Claude checks for intervening edits to the repository file. You can ask it to edit that file directly instead. Temporary work is applied or discarded with you at session end. Tracking the file in Git is your choice.

Ask to preview your answers to open a local board. It shows the official criteria, your answers and justifications, and evidence links. Each board covers one badge section. You can read all criteria together or choose a response category such as Unmet. A table of contents helps you move through the list.

The board is a local plugin feature outside the MCP’s scope. Claude rerenders it after draft changes; the open HTML refreshes automatically to show the regenerated snapshot. Reading or navigating it does not change an answer. Discuss revisions in the conversation. During an interactive revision, Claude updates the justification first and keeps the response unchanged while you review the wording. After you approve it, Claude updates the response. Initial drafts can include both together.

## Submitting answers

Claude offers the available submission paths and follows your preference:

- **Proposal URLs:** open your proposed answers in the official edit form, with changes highlighted for review. Nothing is saved by opening a link.
- **A repository `.bestpractices.json`:** commit the exported file so the badge site can read it as automated-tool input. The site fills blanks and flags differences for review without overwriting answers a person has already recorded.

You review and save the website form. Claude may help with login or saving only when you explicitly ask it to perform that action. The MCP server does not authenticate or write to the badge site. Console-fill scripts are no longer provided. See the [submission guide](skills/ossf-bp-badges/references/application.md#website-transfers) for details.

## OpenSSF Scorecard

Ask **“Explain my Scorecard findings”**, **“Set up a Scorecard badge”**, or **“Fix the unpinned actions reported by Scorecard.”** The [Scorecard skill](skills/ossf-scorecard/SKILL.md) reads published results, investigates findings, and helps implement improvements. It can configure the official Scorecard Action when you want to publish results. An existing public result may already support a badge without adding an Action.

Scorecard work needs no local Scorecard installation or Best Practices registration. The API returns an existing published result; fetching it does not start a scan. After changes reach your remote repository, Claude checks for a newer published result before reporting an effect on the score. It reports any limits on coverage or comparison.

Implementation and publication guidance covers public GitHub repositories. The controller can also read existing GitLab API results, including subgroup repositories, and import upstream Scorecard JSON from a file or standard input. Those imports do not publish results. See the [publication guide](skills/ossf-scorecard/references/action-publication.md) and [diagnostic options](skills/ossf-scorecard/references/authentication-and-results.md#optional-upstream-cli-diagnostics).

## GitHub workflow maintenance

Ask **“Audit my GitHub Actions workflows”**, **“Pin my actions to full SHAs with version comments”**, or **“Move workflow writes to the jobs that need them.”** The [workflow maintenance skill](skills/github-workflow-maintenance/SKILL.md) works independently of Scorecard and badge registration.

It reviews action versions and pins, job permissions, reusable workflows, and existing Dependabot or Renovate coverage. It can implement the changes you request and explain their effects. Repository settings, such as SHA enforcement or action allowlists, are proposed separately so you can assess their compatibility and maintenance cost. The skill reports what it checked and what remains unverified.

## Test coverage

Ask **“Help me get a coverage badge”**, **“Establish a coverage baseline”**, or **“Find worthwhile tests for our uncovered code.”** The [coverage baseline skill](skills/coverage-baseline/SKILL.md) helps you measure your tests, publish a report, and add a badge that lets visitors see how much of your code the tests exercise. Getting that badge working is a useful first step toward better testing.

The guidance starts with your existing test runner, includes untested source files, and explains the coverage metric your tool measures. Alongside Python and JavaScript examples, a [language guide](skills/coverage-baseline/references/languages.md) covers Go, Rust, Java/Kotlin, .NET, C/C++, Swift, Ruby, and PHP. A Python GitHub Actions template demonstrates running tests and sending the report to Codecov; other languages can use the same reporting and badge steps with their own test commands and report formats. Local HTML reports and CI artifacts are also supported.

The badge links to the report for the intended branch so visitors can explore the result. The same measurements help with OpenSSF's statement- and branch-coverage criteria, and the skill explains which measurements each criterion needs.

The [coverage-tool license guide](skills/coverage-baseline/references/licenses.md) lists license names and OSI approval status for the recommended tools, separately from Codecov's hosted service.

## Static analysis

Ask **“Help me add a code-analysis badge”**, **“Configure CodeQL”**, **“Set up Bandit for our Python code”**, or **“Should we use Snyk Code or Snyk Open Source?”** The [static analysis skill](skills/static-analysis/SKILL.md) helps choose a tool that fits your project, get the first scan running, and add a badge linked to its results. It explains source-code checks and dependency vulnerability checks in plain language.

It covers CodeQL default and advanced setup, a Python workflow example, Bandit configuration, Snyk's product choices, and [practical starting tools for other languages](skills/static-analysis/references/languages.md). The skill helps you work through the first findings without getting overwhelmed. Coverage and static-analysis work need no OpenSSF registration.

A workflow badge shows whether the analysis job passed, while the linked results show what it found. The skill explains that distinction when adding the badge and helps turn findings into fixes. Scan history and those fixes also support the relevant OpenSSF static-analysis criteria.

The [analyzer license guide](skills/static-analysis/references/licenses.md) lists license names and OSI approval status, including which parts of CodeQL and Snyk are open source and which use separate product terms.

## Development

From the repository root:

```bash
make setup
make check
make plugin-validate
```

The local board and Scorecard helper use only the Python standard library; BadgeApp operations use the separately installed MCP package. The root Makefile runs all plugin and maintenance tests, then compiles the Python sources. Plugin validation requires the Claude Code CLI. See the repository [README](../../README.md) for the layout.

The plugin’s [`.mcp.json`](.mcp.json) registers the pinned server. Discovery, criteria, public progress, draft construction/checks and proposal URLs use its tools. Optional `read_draft` and `update_draft` calls use server-managed storage; they are not required for caller-owned documents. See the [application guide](skills/ossf-bp-badges/references/application.md) for the mapping and host responsibilities.

The standalone board renderer accepts explicit files and never contacts BadgeApp:

```bash
venv/bin/python plugins/badge-buddy/scripts/review_board.py \
  --input /path/to/draft.json \
  --output /path/to/board.html \
  --project-id 16754 --section baseline-1 --view all
```

It reports a local HTML URL; add `--open` to open it directly. It supports all six badge sections. Rerun it after editing the input JSON. The board displays a snapshot using the bundled catalog and does not compare saved and proposed values automatically.

The Scorecard controller supports `fetch --repo owner/repo --output <path>`, `explain --input <path>`, and `diff --before <path> --after <path>`. It preserves published results and compares them without recomputing the upstream score.

The bundled [BadgeApp questionnaire](assets/examples/badgeapp/README.md) is a dated worked example with provenance and licensing information. Its answers describe BadgeApp and are not copied into another project's assessment.

For catalog updates, `make refresh-upstream BADGE_REPO=/path/to/clone` downloads the public application pages and verifies a candidate catalog before replacing the bundled one. Ordinary plugin use reads the bundled assets. See [criteria maintenance](../../docs/criteria-maintenance.md) for the full procedure.

---

Badge Buddy includes material from the OpenSSF Best Practices badge contributors and the OpenSSF Security Baseline and Scorecard projects. See [third-party notices](../../THIRD_PARTY_NOTICES.md) for attribution, sources, and licensing information.

OpenSSF® is a trademark of The Linux Foundation. “OpenSSF Best Practices” refers to the badge program operated at [bestpractices.dev](https://www.bestpractices.dev/), and “OpenSSF Scorecard” to the project at [scorecard.dev](https://scorecard.dev/). Badge Buddy is an independent tool for working with those programs.
