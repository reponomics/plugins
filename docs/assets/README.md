# Common Thread banners

The Reponomics marketplace and its plugins share the Common Thread identity ("Common Thread" is the informal/internal name for the chosen theme): warm paper or deep petrol backgrounds, bold typography, a connecting blue thread, and softly dimensional imagery. The marketplace and plugin banners use the monochrome skyline wordmark without a trailing period. Release Buddy uses the approved centered package with cords resting on the floor.

## Files

Each banner set has its own folder; the marketplace banners are in `marketplace/` and the shared wordmark in `wordmark/`. Every entry is available as both `.png` and `.svg`.

| Artwork | Folder | Light filename stem | Dark filename stem | Dimensions |
| --- | --- | --- | --- | --- |
| Marketplace README | `marketplace/` | `marketplace-light-840x240` | `marketplace-dark-840x240` | 840 × 240 |
| Badge Buddy README | `badge-buddy/` | `badge-buddy-light-840x240` | `badge-buddy-dark-840x240` | 840 × 240 |
| Starter Buddy README artwork | `starter-buddy/` | `starter-buddy-light-840x240` | `starter-buddy-dark-840x240` | 840 × 240 |
| Release Buddy README | `release-buddy/` | `release-buddy-light-840x240` | `release-buddy-dark-840x240` | 840 × 240 |
| Workflow Guard README | `workflow-guard/` | `workflow-guard-light-840x240` | `workflow-guard-dark-840x240` | 840 × 240 |
| Badge Progress README | `badge-progress/` | `badge-progress-light-840x240` | `badge-progress-dark-840x240` | 840 × 240 |
| Marketplace large format | `marketplace/` | `marketplace-light-1280x640` | `marketplace-dark-1280x640` | 1280 × 640 |
| Standalone wordmark | `wordmark/` | `reponomics-wordmark-light` | `reponomics-wordmark-dark` | 760 × 130 (PNG at 2×, transparent) |

## Format details

All fourteen banner SVGs are editable. Each embeds the Common Thread artwork with the lettering removed and draws everything else on top:

- Plugin signatures and the large marketplace wordmarks all reference `../wordmark/reponomics-wordmark-skyline-{light,dark}.svg#wordmark`: the monochrome skyline lettering without a trailing period. Editing that shared pair updates the wordmark across all fourteen banners when the PNGs are regenerated.
- Plugin titles and taglines are live `<text>` in Helvetica Neue: Bold 62 px for titles and Regular 28 px for taglines, on the same baselines in every plugin banner. Keep titles within about 450 px so they clear the artwork.
- The marketplace tagline is live `<text>` in Helvetica Neue Regular.

To change text, edit it in both theme files (and the `<title>` element, which screen readers use) and regenerate the PNGs. The text needs the font installed where it is rendered; Helvetica Neue ships with macOS, and other systems fall back to Helvetica or Arial.

Because the banners reference the wordmark in a sibling folder, a banner SVG viewed directly may show without it: GitHub shows an SVG as an isolated image, and librsvg (and so `rsvg-convert` run by hand) only loads referenced files from the SVG's own folder or below. `make render-assets` renders each banner from a temporary copy with the wordmark folder placed where librsvg accepts it. The READMEs use the PNGs, which have the wordmark rendered in.

### Replacing the wordmark

1. Edit `wordmark/reponomics-wordmark-skyline-{light,dark}.svg` for the shared wordmark across plugin and marketplace banners. Preserve the artwork coordinates inside `<g id="wordmark">`; the banner transforms position that group directly, independently of the outer SVG viewBox.
2. Run `make render-assets`. It regenerates the wordmark PNGs and every banner.

The original non-skyline wordmark SVGs are vector paths traced from the large dark marketplace wordmark, with the `i` dot and the period as circles. The light variant uses ink `#00222F` and amber `#F1A01E`; the dark variant uses warm white `#FBF9F5` and amber `#F1AF4A`. Because it is a trace of generated lettering rather than a font, some stem tops show slight irregularities at large sizes.

The Badge Buddy, Starter Buddy and Release Buddy artwork was extracted from the approved presentation sheet and modestly enlarged to 840 × 240. The marketplace banners were separately recomposed for both aspect ratios using the built-in image-generation tool, then exported at their exact target dimensions. The wide marketplace images were trimmed vertically before resizing, preserving their proportions and full content. The image generator rendered the light-theme marketplace lettering with slightly different letterforms, so the light marketplace banners carry the dark banners' wordmark, tagline and signature, recolored to the light palette.

Use the 840 × 240 files for README headers and the 1280 × 640 marketplace files for the larger 2:1 format. Both themes are explicit assets; theme selection belongs to the consuming README or page.

## Regenerating the PNGs

The selected skyline treatment is `wordmark/reponomics-wordmark-skyline-{light,dark}.svg`: monochrome lettering and `i` dot, with no trailing period. The light version uses `#00222F`; the dark version uses `#FBF9F5`. Both have transparent 2× PNG exports alongside them. Both skyline files share `viewBox="5.12 0.25 738.59 142.25"`, fitted to the artwork with an approximately 8-unit transparent inset on every side. This removes the unused space left by the period while giving the spire breathing room. In layouts, allow approximately one `i`-dot diameter (28.38 SVG units, scaled with the logo) between the artwork and neighboring content; count the built-in inset toward that space. Supply the remaining spacing through CSS or the surrounding composition. Embedding the `#wordmark` group directly does not include the outer SVG viewport padding, so provide the full clear space in that case.

The optional `wordmark/reponomics-wordmark-{light,dark}-i-{blue,amber}.svg` variants remove the trailing period and color the dot of the `i`. Blue uses `#2F81F7` in both themes; amber uses `#F1A01E` for light and `#F1AF4A` for dark. Each has a transparent 2× PNG alongside it. They preserve the original lettering, dimensions, and `wordmark` group ID. These color explorations are not used by the current banners.

After editing an SVG, run `make render-assets` from the repository root; [CONTRIBUTING.md](../../CONTRIBUTING.md#readme-artwork) covers the command and the tools it needs. Banners render at their native size; wordmarks render at 2× with a transparent background. With `pngquant` and `oxipng` installed, each PNG is reduced to a 256-colour palette at pngquant quality 90–100 and recompressed losslessly; at actual size the result is visually identical. The SVGs embed images compressed the same way, so re-rendering does not degrade them further. Text added in an editor in a font other than Helvetica Neue should be converted to paths, since `rsvg-convert` substitutes whatever fonts are installed.

## Generation record

[generation-prompts.json](generation-prompts.json) records the marketplace composition prompts and the plugin export method. The approved artwork was generated with the built-in image-generation tool; ImageMagick handled crop, resize, and PNG export. The banners' lettering was later replaced with live text and references to the wordmark files over the same artwork.

The Workflow Guard and Badge Progress illustrations were generated as text-free light/dark pairs, cropped proportionally to the README dimensions, and combined with editable titles, taglines and the shared skyline signature. Their [generation prompts](mod-banner-prompts.json) record the artwork specifications.
