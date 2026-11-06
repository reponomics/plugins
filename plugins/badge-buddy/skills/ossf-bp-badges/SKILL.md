---
name: ossf-bp-badges
description: Use when the user mentions badges in relation to OpenSSF, OSSF, open source security, Best Practices, CII, bestpractices.dev, Security Baseline, OSPS, or Baseline levels 1-3. Help explain criteria, complete badge applications, and implement project improvements.
allowed-tools: Bash("${CLAUDE_PLUGIN_ROOT}/scripts/ossf.py" *), Bash(${CLAUDE_PLUGIN_ROOT}/scripts/ossf.py *)
license: MIT (See ${CLAUDE_PLUGIN_ROOT}/THIRD_PARTY_NOTICES.md for attribution regarding OpenSSF)
metadata:
    author: Reponomics
---

# OpenSSF Best Practices

Work alongside the user to understand the criteria, complete their application, and make improvements they choose. The form belongs to the user: they decide what to record and submit. Your role is to help, with no authority to approve their answers or award a badge. Follow the requested scope: a question, one answer, or a whole badge section. Passing is a substantial achievement; partial progress is useful too.

Act in good faith: these badges are self-reported. Take the user at their word about their project, including statements you cannot independently verify, and use their account directly when drafting. If a statement appears inconsistent with known facts or a criterion, assume clarification is needed. Explain the specific discrepancy, allow for missing context or a mistake in your own interpretation, and help resolve the misunderstanding without vetting the user's honesty. Help supply the details or links the criterion asks for without adding your own evidence requirements or making your approval a condition of proceeding.

Preserve the distinction between current practices, plans, and history: a newly written policy does not establish a history of following it, and local changes may still need to be published. The user's account can supply history or context that the repository does not show.

## Choose the relevant badge

Honor the user's choice or resume their existing work. For a new application, suggest Passing for Metal or the lowest unfinished Security Baseline level. The tracks are parallel; users may work on later levels before earning earlier badges. Ask which section they want only if the task requires that choice and it remains unclear.

| Badge | Catalog section | Reference |
| --- | --- | --- |
| Passing | `passing` | [Passing](references/passing.md) |
| Silver | `silver` | [Silver](references/silver.md) |
| Gold | `gold` | [Gold](references/gold.md) |
| OSPS / Security Baseline | `baseline-1`, `baseline-2`, `baseline-3` | [Baseline](references/baseline.md) |

When beginning a level or explaining its prerequisites and completion, read that reference's Scope section. For an individual criterion, read its entry and applicable section notes. Follow a thematic link only when its stated question arises. Reuse guidance and criterion records already read during the session.

For OpenSSF Scorecard requests, use `ossf-scorecard`; it is a separate program based on automated checks.

For implementation work, use [coverage-baseline](../coverage-baseline/SKILL.md) to measure test coverage and add meaningful tests, or [static-analysis](../static-analysis/SKILL.md) to select, configure, and triage source-code analyzers. Carry the selected criterion and agreed scope into that work, then return with measured evidence. Installing a tool or writing a workflow alone does not establish a criterion's coverage, use, or remediation requirements.

## Interpret and answer criteria

Retrieve the complete record for the selected section and criterion using the lookup below, then read its entry in the badge reference. Include description, details, applicability, and required justification or URL fields in the interpretation. Repeated Metal identifiers share stored answers but can have different requirements at each level; reassess an inherited answer against the selected level before relying on it.

| Answer | Meaning |
| --- | --- |
| `Met` | The project implements the required practice. A file or tool alone may not establish its use, measured results, or history. |
| `Unmet` | An applicable practice is not satisfied. Offer help with useful improvements. |
| `?` | The answer is unknown. A limited search that finds nothing does not establish absence. |
| `N/A` | The criterion permits it and its applicability conditions are absent. Include the required explanation. |

For Metal badges, every applicable MUST or MUST NOT must be satisfied. A SHOULD practice that the project has chosen not to adopt is `Unmet`, but can count toward the badge with a justification explaining the decision and its implications. A SUGGESTED practice counts as complete with either `Met` or `Unmet`. Preserve these distinctions; raw answer counts are not badge percentages.

For a full section, collect shared project information once and reuse it across related criteria. Draft answers from that information, including the user's account, and group remaining questions by subject. Repository searches can help find details and links; an unsuccessful search does not invalidate something the user has told you. Present criteria in official order without turning each one into a separate interview question. Preserve existing answers, including `?` and empty justifications, unless the user requests changes or resolves a synchronization difference.

### Look up selected criteria

Resolve the [bundled catalog](../../assets/criteria/criteria.json) relative to this skill. With Python 3.11+, the following command returns only the requested records, accepting form IDs or Baseline display IDs. Replace the path, section, and IDs for the current task; several IDs from one section can be retrieved together. No registration or application setup is needed.

```bash
python3 - "<absolute path to criteria.json>" passing dynamic_analysis <<'PY'
import json
import sys
from pathlib import Path

catalog_path, section, *criterion_ids = sys.argv[1:]
sections = json.loads(Path(catalog_path).read_text(encoding="utf-8"))["sections"]
if section not in sections or not criterion_ids:
    raise SystemExit("Supply a valid section and at least one criterion ID")
for criterion_id in criterion_ids:
    matches = [record for record in sections[section]
               if criterion_id in (record["id"], record.get("display_id"))]
    if len(matches) != 1:
        raise SystemExit(f"Expected one criterion for {section}/{criterion_id}; found {len(matches)}")
    print(json.dumps({"section": section, "criterion": matches[0]}, ensure_ascii=False, indent=2))
PY
```

Use the bundled criteria during ordinary application work. If the user reports a difference or the form shows different wording, compare that specific criterion and follow the current form's requirement.

## Draft and review

Before drafting application text, read [justification style](references/justification-style.md) for wording, required detail, and short examples from BadgeApp. Explanations of criteria do not require application-writing review.

When the requested draft is ready, ask a second agent to review your work: your interpretation, writing, and handling of the user's instructions and account. Give it the user's request and relevant interaction context, the changed answers, their complete criteria, relevant project and user information, the style guide, and [peer-review instructions](references/peer-review.md). The form supplies context for reviewing your contribution; it is not being submitted for the reviewer's approval. Apply useful corrections before presenting or recording the text. Scope review to your contribution, whether one answer or a whole draft. Honor requests to skip or stop review; if a second agent is unavailable, review your own work using the same guidance and say so briefly.

## Work with the application

Before the first application operation, resolve the [invocation paths](#invocation-paths), then read [Start or resume](references/application.md#start-or-resume) and select the working assessment. After startup, read only the section for the current task:

| Task | Instructions and purpose |
| --- | --- |
| Start or resume | [Start or resume](references/application.md#start-or-resume): choose the working file, resolve the project, and synchronize once |
| Use a repository assessment | [Repository assessments](references/application.md#repository-assessments): select a working copy and preserve changes on writeback |
| Record agreed answers | [Record answers](references/application.md#record-answers): apply status and wording changes |
| Show answers or preview a revision | [Preview](references/application.md#preview): open the board or isolate undecided wording |
| Export JSON | [Export](references/application.md#export): write the selected assessment to a file |
| Update the badge website or explain a transfer | [Website transfers](references/application.md#website-transfers): choose or use the requested transfer method |
| Explain an API or field-format issue | [API](references/application.md#api): request formats and field-name differences |
| End the session | [Stop](references/application.md#stop): retain saved work and dispose of unfinished previews |

Questions and project improvements do not require registration. The controller supports GitHub-hosted projects; for other forges, explain criteria and draft answers without invoking it or claiming synchronized status.

### Invocation paths

Resolve [the controller](../../scripts/ossf.py) relative to this skill and retain its absolute path. Other bundled links are relative to their containing document. Select the repository from the user's request and session context; `git rev-parse --show-toplevel` supplies the current checkout's root.

Claude Code substitutes `${CLAUDE_PLUGIN_DATA}` with the plugin's persistent data directory. Use that value for `--data-dir`. This is the command template for the single startup operation described in the application guide:

```bash
"<controller-path>" --repo "<project-root>" --data-dir "${CLAUDE_PLUGIN_DATA}" status
```

Replace placeholders with concrete absolute paths and quote shell arguments. Retain these paths for subsequent commands and delegated work. When using a selected assessment file, add `--assessment-file "<working-file>"` to every operation. Keep each repository's answers separate.
