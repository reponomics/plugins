# Contributing

Please help contribute to this project by filing Issues if you encounter any difficulties or have suggestions for concrete improvements. If you discover any technical problems, either in the functionality of the plugin, or the accuracy of the information provided by Claude while using it, please open a Bug Report and let us know.

We strongly encourage contributions from users who host their projects outside of GitHub, so that we can provide more targeted support and platform-specific information for other source forges.

All contributors must agree to follow the project's [Code of Conduct](./CODE_OF_CONDUCT.md).

## Local development checks

Use Node.js 24 through nvm, then install the local Git hooks:

```sh
nvm use
make hooks-install
```

`make hooks-install` creates `venv`, installs the pinned Python development dependencies, runs `npm ci --ignore-scripts`, and installs the pre-commit and pre-push hooks. Initial installation downloads dependencies and populates local caches; subsequent checks normally run offline unless dependencies or caches change. Node and npm must be on your Git client's PATH, including when committing from an editor.

Before a commit, Ruff formats Python and Prettier formats supported Markdown, JSON, YAML, JavaScript, CSS, and HTML files. Syntax and merge-conflict checks also run. Only staged files are selected; a formatter can change the whole selected file. Markdown prose is not hard-wrapped, and embedded code examples are not reformatted. Formatting excludes licenses, downloaded snapshots, third-party reference material, fixtures, and artwork. If a formatter changes a file, review the diff and stage the changes before retrying the commit. Pre-commit temporarily saves unstaged changes and restores them afterward; if those changes conflict with a formatting fix, resolve the partial staging before retrying.

To run the commit checks explicitly against staged files:

```sh
make hooks-check
```

Before pushing, Treestamp checks the README's curated directory tree against the Git index, even when the README itself has not changed. It reports drift without rewriting the document. Stage additions, deletions, and renames first, then check or refresh the tree using its saved visibility settings:

```sh
make treestamp-check
make treestamp-update   # When needed; review and stage the README afterward.
```

To change which entries are shown, open the editor with `venv/bin/treestamp --load README.md`. Prettier leaves the generated Treestamp block alone.

The pre-push hook also runs `make check`, which executes the full local test suite and compiles Python sources. These checks cover the current checkout and index; they do not verify every commit selected by an arbitrary push refspec. Run the tests directly when preparing a change for review:

```sh
make check
```

Plugin validation remains a manual check and requires the Claude CLI:

```sh
make plugin-validate
```

For an intentional work-in-progress push only, `SKIP=tests git push` explicitly skips the test hook. Run `make check` before presenting the change as ready for review. To remove the installed hooks, run `make hooks-uninstall`.

## README artwork

The banners and wordmark in [`docs/assets/`](docs/assets/) are maintained as SVGs, with one folder per plugin plus `marketplace/` and `wordmark/`, and the PNGs that the READMEs display are generated from them. The banner titles and taglines are live text, so they can be changed by editing the `<text>` elements in both the light and dark SVG. Every banner draws the skyline wordmark from `wordmark/reponomics-wordmark-skyline-light.svg` and `wordmark/reponomics-wordmark-skyline-dark.svg`, so replacing those two files changes it everywhere; the [asset README](docs/assets/README.md#replacing-the-wordmark) lists what a replacement needs.

After editing an SVG, regenerate its PNG and commit both files:

```sh
make render-assets                                     # every SVG under docs/assets/
make render-assets SVG=docs/assets/release-buddy/release-buddy-dark-840x240.svg
```

`make render-assets` runs [`tools/render-assets.sh`](tools/render-assets.sh), which can also be called directly with SVG files or folders as arguments. It requires `rsvg-convert` from librsvg (`brew install librsvg` on macOS, `apt install librsvg2-bin` on Debian and Ubuntu) and stops with an error if it is missing. If `pngquant` and `oxipng` are installed (`brew install pngquant oxipng`), the PNGs are also compressed; without them the script still renders, but the files are about twice as large. The banner text is set in Helvetica Neue, which ships with macOS; on other systems it falls back to Helvetica or Arial, so render published artwork on a machine that has the font. See the [asset README](docs/assets/README.md) for sizes and file details.
