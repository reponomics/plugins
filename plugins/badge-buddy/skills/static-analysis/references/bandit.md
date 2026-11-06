# Bandit for Python

Bandit examines Python syntax trees for common insecure patterns. It is useful as a small local/CI check; it does not audit dependencies, exercise runtime behavior, or prove that all dangerous data flows are absent. Start with the project's Python virtual environment and existing development dependency mechanism. Pin a reviewed compatible Bandit release through that mechanism instead of installing a floating version on every run. [Bandit overview](https://bandit.readthedocs.io/en/latest/)

## Select source and configuration

Inventory production modules, entrypoints, automation scripts, and tests. Start with all maintained Python source; omit vendored/generated code only with a documented reason and owner. The [configuration example](../assets/templates/bandit.yaml) excludes only local virtual environments. Adapt their actual locations. Do not blanket-exclude tests: test utilities can still invoke subprocesses, handle secrets, or process unsafe data.

Pass YAML/TOML explicitly with `-c`; a `pyproject.toml` section is not automatically active. TOML configurations can require the `bandit[toml]` extra. Begin with default rule selection; avoid copying an arbitrary `tests` allowlist or `skips` list. If a finding is demonstrably safe in context, use a specific suppression such as `# nosec B603` with an adjacent rationale. A bare `# nosec` hides every finding on the line. [Bandit configuration](https://bandit.readthedocs.io/en/latest/config.html)

For a project with `venv`, incorporate the command in its existing Makefile, preserving its annotated auto-generated help target. Use tool/path variables; for example, `PYTHON ?= venv/bin/python`, `BANDIT_CONFIG ?= bandit.yaml`, and `BANDIT_TARGETS ?= .`, with a `security-scan: ## Run Python security analysis` recipe:

```makefile
	$(PYTHON) -m bandit -c $(BANDIT_CONFIG) -r $(BANDIT_TARGETS)
```

This is the scan invocation, not a complete CI health check. Review the scanner's error/skipped-file section as well as its findings. For unattended enforcement, validate structured output as described below. Respect an existing environment name instead of replacing it.

## Baseline and incremental enforcement

Run a full initial scan and save JSON to an explicit path:

```bash
venv/bin/python -m bandit -c bandit.yaml -r . -f json -o bandit-initial.json
```

This command can exit nonzero when it finds issues; retain and inspect the report before deciding whether the run failed operationally. Check its `errors` list, expected file metrics, and findings. Missing or empty source analysis must not be accepted as success merely because no issues were returned.

After triage, a reviewed JSON baseline can support comparison with `-b bandit-baseline.json`. Keep its tool/config/scope provenance and an issue owner; it records deferred findings, not proof they are safe. Refresh it only through reviewed changes. Line motion and tool changes can affect comparison. The CLI also offers severity and confidence filters; apply an agreed gate without discarding the full findings queue. [Bandit command options](https://bandit.readthedocs.io/en/latest/man/bandit.html)

When integrating CI, capture the scan status, validate that a fresh JSON report exists and has the expected schema, fail on report `errors` or absent intended source metrics, then apply the agreed finding policy. Test this with clean source, a known detectable pattern, a syntax error, and a missing target. Bandit can report skipped/invalid files independently of findings; a clean exit alone is insufficient evidence of scan completeness. Keep report upload separate from gating and preserve failures after upload. Do not add `--exit-zero` or `|| true` to make the job green, and do not import another scanner's exit-code meanings into Bandit.

Retain reviewed exceptions and revisit them when surrounding code changes. Follow the shared [baseline and gate procedure](baseline-and-gates.md) for debt ownership, report visibility, and a truthful workflow-status badge.
