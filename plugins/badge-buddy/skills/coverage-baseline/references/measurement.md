# Establishing a trustworthy baseline

## Python: coverage.py with the existing test runner

Prefer the repository's configured pytest-cov integration if it already exists. Otherwise coverage.py can run pytest or unittest without adding another wrapper. Add development dependencies through the existing manifest/lock process and reuse the project environment. Do not replace a working dependency workflow with an ad hoc `pip install` in CI.

Adapt this `pyproject.toml` fragment to the actual production roots. `src` is an example, not a safe default for every repository:

```toml
[tool.coverage.run]
branch = true
source = ["src"]
relative_files = true

[tool.coverage.report]
show_missing = true
precision = 2

[tool.coverage.xml]
output = "coverage.xml"

[tool.coverage.html]
directory = "htmlcov"
```

An explicit `source` lets coverage.py find unexecuted importable files. Verify namespace packages and unusual layouts against the report; set the applicable installed-version options when necessary. `relative_files` helps normalize paths across environments but does not make incompatible data sets safe to combine. See [source selection](https://coverage.readthedocs.io/en/latest/source.html) and the [configuration reference](https://coverage.readthedocs.io/en/latest/config.html).

Merge a target like this into the existing Makefile, retaining its conventions and help generator. The commands deliberately stop on test failure instead of presenting a partial run as a successful baseline:

```makefile
VENV ?= venv
PYTHON ?= $(VENV)/bin/python

.PHONY: coverage help
coverage: ## Run the full test suite and write coverage reports
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m pytest
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage xml
	$(PYTHON) -m coverage html

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
```

For unittest, replace the run command with `$(PYTHON) -m coverage run -m unittest discover -s tests`. Keep runner-specific settings and test selection identical to the normal full suite. Ignore generated `.coverage*`, `htmlcov/`, and `coverage.xml` in version control as appropriate without accidentally ignoring a tracked `.coveragerc`. For multiprocess tests, consult the installed coverage/pytest-cov version's subprocess instructions and verify a child-process-only branch appears before claiming complete measurement.

With branch measurement enabled, the displayed total counts statements and branch destinations together. Use XML/JSON data to distinguish statement and branch metrics; do not call the combined percentage “branch coverage.” After several consistent runs, `fail_under` can enforce a chosen total floor, with `precision` affecting decimal comparison. See [branch measurement](https://coverage.readthedocs.io/en/latest/branch.html).

## JavaScript and TypeScript

Preserve the existing runner and transforms. For Vitest, install a coverage provider version compatible with the installed Vitest version using the project's package manager and lockfile; avoid an implicit interactive provider install in CI. Merge this fragment into the existing configuration:

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{js,jsx,ts,tsx}'],
      exclude: ['src/**/*.d.ts', 'src/**/*.{test,spec}.{js,jsx,ts,tsx}'],
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: 'coverage',
    },
  },
});
```

Adapt extensions, include patterns, and justified exclusions to the real codebase. An explicit `coverage.include` is necessary to report never-imported production files in current Vitest. Exclusion configuration can replace defaults, so check the installed major version rather than copying obsolete `coverage.all` settings. Keep an npm script such as `"coverage": "vitest run --coverage"`; run `npm ci` then `npm run coverage` in CI. Verify a never-imported module and mapped TypeScript lines in the report. See [Vitest coverage](https://vitest.dev/guide/coverage.html).

For Jest, merge coverage settings instead of introducing Vitest:

```js
// Merge into the existing Jest configuration, preserving transforms and environment.
module.exports = {
  collectCoverageFrom: ['src/**/*.{js,jsx,ts,tsx}', '!src/**/*.d.ts'],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'html', 'lcov'],
};
```

Use a script such as `"coverage": "jest --coverage --runInBand"` for a simple deterministic baseline; keep an existing tested parallel setup when appropriate. Verify source globs match actual files. Jest's `coverageThreshold` can enforce separate metrics after baseline review. See [Jest configuration](https://jestjs.io/docs/configuration#collectcoveragefrom-array).

For another ecosystem, use the [language-specific starting points](languages.md) with its existing test runner and supported export formats. Do not reinterpret line, statement, branch, or function percentages as interchangeable. Record the instrumenter/provider when comparing runs; changes in instrumentation or source mapping can change results without any change in test quality.

## Baseline record

Use a compact table or project note containing commit, runtime/tool versions, command, tested components, included roots, exclusions with reasons, metric names and values, report paths, and test result. Add three to five prioritized gaps with a behavior to test, its risk, and the expected assertion. Preserve an honest “not measured” entry for components outside the run.
