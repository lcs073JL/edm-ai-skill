---
name: edm-ai
description: Process Adobe Illustrator EDM/email designs that use slice areas into 2x JPEG slice assets and responsive HTML. Use when the user asks to export an Illustrator EDM, normalize EDM slices, create responsive email HTML, wrap sliced JPEGs in HTML, or repeat the NAC-style EDM slice-to-HTML workflow for .ai files with 1-column, 2-column, or 3-column slice rows.
---

# EDM AI

## Workflow

Use this workflow for Illustrator EDM files with slice rectangles named `"<Slice>"`.

1. Confirm the active Illustrator document with `get_document_info`.
2. Read slice objects with `find_objects` using `name:"<Slice>"`, `type:"path"`, `coordinate_system:"artboard-web"`.
3. Save a backup before modifying the `.ai` file.
4. Normalize obvious content-grid slice rectangles only:
   - 1-column row: `x=0`, `width=660`
   - 2-column row: `x=0 width=330`, `x=330 width=330`
   - 3-column row: `x=0 width=220`, `x=220 width=220`, `x=440 width=220`
5. Preserve intentionally uneven footer, legal, utility, or CTA rows when their slice widths appear deliberate.
6. Keep row heights from the artwork, but make normalized slices in the same row share the same `y` and `height`.
7. Save the Illustrator document.
8. Export slices as JPEG at 2x scale from Illustrator. If the MCP `export` tool fails to create files, run an Illustrator JSX script via `osascript` with `ExportOptionsJPEG`, `horizontalScale=200`, `verticalScale=200`, `qualitySetting=100`, and `artBoardClipping=true`.
9. If named social icon groups are present, export them from Illustrator as transparent PNGs into the same `images/` folder.
10. Generate responsive email HTML with `scripts/build_edm_html.py`, then remove any generated `<title>` tag unless the user explicitly asks for one.
11. If social icon PNGs were exported, replace the sliced social-bar row in `index.html` with an email-safe social icon table.
12. If named footer legal text objects or groups are present, replace the sliced footer legal row with real HTML text links.
13. If links are needed, create a `links.csv` link map and apply it with `scripts/apply_edm_links.py`.
14. Verify all image references exist and inspect split-column image dimensions.

## Single-Slice Re-Export

When the user changes artwork in Illustrator and asks to refresh one slice in the HTML output, use the exported HTML image filename as the source of truth, not the Illustrator slice number. For example, if the changed Illustrator area is referenced in HTML as `images/slice_08.jpg`, re-export and replace `slice_08.jpg`.

Guidelines:

- Sort current Illustrator `<Slice>` rectangles by visual order (`y` ascending, then `x` ascending) to map `slice_01.jpg`, `slice_02.jpg`, etc. to the exported files.
- Re-export only the target slice bounds into the existing `edm-export/images/` folder, preserving the same filename so existing HTML and links continue to work.
- Leave `index.html` and `links.csv` unchanged unless the target filename or link itself changed.
- If Illustrator `imageCapture` writes PNG data despite a `.jpg` extension, convert the refreshed file back to a real JPEG before finishing.
- Verify the refreshed file exists, is a JPEG, keeps the expected 2x dimensions, and is still referenced by `index.html`.

## Row Detection

Sort slices by `y` ascending, then `x` ascending.

Group slices into the same row when their vertical spans overlap substantially or their `y` values are very close. For each row:

- 1 slice means a 1-column row.
- 2 slices means a 2-column row.
- 3 slices means a 3-column row.
- Any other count needs user review before modifying.

Use the row's minimum `y` and maximum bottom edge to calculate the unified row height.

Tiny Illustrator float noise such as `660.00002` is acceptable after modification.

## Uneven Footer Slices

Do not blindly force every multi-slice row into equal columns.

Preserve original slice widths when a row looks intentionally uneven, especially near the EDM footer or utility area. Common signals:

- The row is near the bottom of the artboard.
- Slice widths are clearly unequal and align with real content such as logos, legal copy, social icons, app badges, address text, unsubscribe links, or terms links.
- Equalizing the row would crop a small element, create an obvious empty area, or move boundaries away from visible artwork.
- The row has many small functional areas or a footer-like layout rather than a content card/grid layout.

Normalize when the row is an obvious content grid and the existing widths are merely off by a few pixels, such as `318/342` for a 2-column row or `224/214/218` for a 3-column row.

When preserving an uneven row, still export it and represent the row in HTML using each slice's actual percentage width based on the 660px canvas. If unsure whether a bottom row is intentional or accidental, ask before modifying it.

## HTML Output

Create an output folder like:

```text
edm-export/
├── index.html
└── images/
    ├── slice_01.jpg
    └── ...
```

Use the Personalise-compatible fluid email markup by default:

- Outer background: default `#F4F4F4` unless the user specifies another color.
- Wrap the EDM in `<center class="outer">` plus a full-width outer table.
- Add a `td` gutter of `padding:0 16px;` around the main container.
- Use an MSO conditional fixed-width `660` wrapper for Outlook:
  `<!--[if mso]><table role="presentation" width="660" align="center" cellpadding="0" cellspacing="0" border="0">...<![endif]-->`
- Main EDM table: `width="100%" class="container"` with CSS `width:100%; max-width:660px;`.
- Every table must include `cellpadding="0" cellspacing="0" border="0"`.
- Use nested row tables for 2-column and 3-column rows so mixed column systems do not fight.
- Image tags: include a fixed `width` attribute and inline CSS like `display:block; width:100%; max-width:660px; height:auto; border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic;`.
- Columns: `width="50%"` for 2 columns, `width="33.333%"` for 3 columns, with `font-size:0; line-height:0; padding:0; margin:0;`.
- Uneven preserved footer rows: use exact percentage widths from the actual slice widths, for example `width / 660 * 100`.
- Do not include a `<title>` tag by default. If the HTML generator adds one, remove it unless the user explicitly provides a title.

This structure is known to render correctly in Singapore Gov Personalise while staying mobile-fluid:

```html
<center class="outer">
  <table role="presentation" width="100%" class="outer" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding:0 16px;">
        <!--[if mso]>
        <table role="presentation" width="660" align="center" cellpadding="0" cellspacing="0" border="0">
          <tr><td>
        <![endif]-->
        <table role="presentation" width="100%" class="container" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="font-size:0; line-height:0; padding:0; margin:0;">
              <img src="images/slice_01.jpg" width="660" alt="" style="display:block; width:100%; max-width:660px; height:auto; border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic;">
            </td>
          </tr>
        </table>
        <!--[if mso]>
          </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</center>
```

## Social Icon Replacement

When the EDM has vector social icons in Illustrator, prefer exporting the icons as separate transparent PNGs and replacing the sliced social-bar row in HTML.

Recommended Illustrator group names:

- `social-facebook`
- `social-instagram`
- `social-linkedin`

Export these named groups as transparent PNGs into the output `images/` folder using stable filenames:

- `facebook-outline-light-40.png`
- `instagram-outline-light-40.png`
- `linkedin-outline-light-40.png`

Use the sliced social-bar row as a placeholder only. After `index.html` is generated, replace the placeholder row with an email-safe centered table on the same red background. Example markup:

```html
<td align="center" style="background-color:#b0232a; padding:12px 0 8px;">
  <table role="presentation" align="center" style="margin:0 auto;">
    <tr>
      <td align="center" style="padding:3px 7px;">
        <a href="https://www.facebook.com/NACSingapore" target="_blank" style="display:block; border:0; text-decoration:none;">
          <img src="images/facebook-outline-light-40.png" alt="Facebook" width="40" style="display:block; width:40px; height:40px; border:0;">
        </a>
      </td>
      <td align="center" style="padding:3px 7px;">
        <a href="https://www.instagram.com/nacsingapore/" target="_blank" style="display:block; border:0; text-decoration:none;">
          <img src="images/instagram-outline-light-40.png" alt="Instagram" width="40" style="display:block; width:40px; height:40px; border:0;">
        </a>
      </td>
      <td align="center" style="padding:3px 7px;">
        <a href="https://www.linkedin.com/authwall?trk=bf&trkInfo=AQGAFrllZduPAQAAAZ4C-yj4g-nEw57wjHZ-rWCeG250hWM5yIWgGFK2Jx1Xgdifito69MxyEWs4eG3IpOSxoaVOgNVu6E5FjaqiyhHP-SUMQQCharyHPvvzHkas9bx32dxplAE=&original_referer=&sessionRedirect=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fnational-arts-council%2F%3ForiginalSubdomain%3Dsg" target="_blank" style="display:block; border:0; text-decoration:none;">
          <img src="images/linkedin-outline-light-40.png" alt="LinkedIn" width="40" style="display:block; width:40px; height:40px; border:0;">
        </a>
      </td>
    </tr>
  </table>
</td>
```

Guidelines:

- Keep the exported PNGs transparent and display them at `40px`, even if the exported source size is slightly larger such as `46 x 46px`.
- Use these default social links unless the user instructs otherwise:
  - `facebook-outline-light-40.png`: `https://www.facebook.com/NACSingapore`
  - `instagram-outline-light-40.png`: `https://www.instagram.com/nacsingapore/`
  - `linkedin-outline-light-40.png`: `https://www.linkedin.com/authwall?trk=bf&trkInfo=AQGAFrllZduPAQAAAZ4C-yj4g-nEw57wjHZ-rWCeG250hWM5yIWgGFK2Jx1Xgdifito69MxyEWs4eG3IpOSxoaVOgNVu6E5FjaqiyhHP-SUMQQCharyHPvvzHkas9bx32dxplAE=&original_referer=&sessionRedirect=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fnational-arts-council%2F%3ForiginalSubdomain%3Dsg`
- Do not guess other campaign-specific URLs.
- Remove the placeholder social-bar slice references from `index.html` after replacement, but leave the source slice files in `images/` unless cleanup is explicitly requested.
- If the named groups are missing, continue with the normal sliced-image workflow and tell the user the social icons could not be exported separately.

## Footer Legal Text Replacement

When the EDM has footer legal items in Illustrator, prefer replacing that sliced footer row with real HTML text links.

Recommended Illustrator text or group names:

- `footer-terms`
- `footer-privacy`

Use these default links unless the user instructs otherwise:

- `footer-terms`: `https://www.nac.gov.sg/terms-of-use`
- `footer-privacy`: `https://www.nac.gov.sg/privacy-statement`

Use white text on the NAC red footer background. Recommended email-safe font stack closest to Futura:

```css
font-family: Futura, Arial, Helvetica, sans-serif;
```

Example markup:

```html
<td align="center" style="background-color:#b0232a; padding:8px 0 10px;">
  <span class="footer-legal" style="font-family:Futura, Arial, Helvetica, sans-serif; font-size:11px; line-height:16px; color:#ffffff;">
    <a href="https://www.nac.gov.sg/terms-of-use" target="_blank" style="color:#ffffff; text-decoration:none;">Terms of Use</a>
    <span style="color:#ffffff;"> | </span>
    <a href="https://www.nac.gov.sg/privacy-statement" target="_blank" style="color:#ffffff; text-decoration:none;">Privacy Statement</a>
  </span>
</td>
```

Add this mobile CSS when using the footer legal text replacement:

```css
@media screen and (max-width: 320px) {
  .footer-legal {
    font-family: Futura, Arial, Helvetica, sans-serif !important;
    font-size: 9px !important;
    line-height: 16px !important;
    color: #ffffff !important;
  }
}
```

Guidelines:

- Use a `|` separator between Terms of Use and Privacy Statement unless the user specifies a different separator.
- Keep desktop/default legal text near `11px` and switch to `9px` at `320px` mobile width.
- Remove the placeholder legal footer slice references from `index.html` after replacement, but leave the source slice files in `images/` unless cleanup is explicitly requested.
- If the named footer legal objects are missing, continue with the normal sliced-image workflow and tell the user the footer legal text could not be replaced automatically.

### Footer Disclaimer Text Replacement

When a footer slice contains the standard NAC newsletter disclaimer, prefer replacing that slice with real centered HTML text on the NAC red footer background.

Use this copy unless the artwork or user provides different text:

```text
This newsletter is brought to you by the National Arts Council.
All information provided is accurate at the time of sending this email.
If you wish to unsubscribe from these emails,
please let us know your email preferences by replying to this email.
```

Recommended markup:

```html
<td align="center" style="background-color:#b0232a; padding:18px 24px 18px;">
  <span class="footer-disclaimer" style="font-family:Futura, Arial, Helvetica, sans-serif; font-size:13px; line-height:21px; color:#ffffff;">
    This newsletter is brought to you by the National Arts Council.<br>
    All information provided is accurate at the time of sending this email.<br>
    If you wish to unsubscribe from these emails,<br>
    please let us know your email preferences by replying to this email.
  </span>
</td>
```

Add this mobile CSS when using the footer disclaimer replacement:

```css
@media screen and (max-width: 320px) {
  .footer-disclaimer {
    font-family: Futura, Arial, Helvetica, sans-serif !important;
    font-size: 6pt !important;
    line-height: 12px !important;
    color: #ffffff !important;
  }
}
```

Guidelines:

- Keep desktop/default disclaimer text at `13px` with `21px` line-height unless the user specifies otherwise.
- Switch the disclaimer to `6pt` with `12px` line-height at `320px` mobile width.
- Preserve manual line breaks from the artwork when they are visibly intentional.
- Remove the placeholder disclaimer slice reference from `index.html` after replacement, but leave the source slice file in `images/` unless cleanup is explicitly requested.

## Link Mapping

Prefer adding EDM links as a final HTML pass after slice export and HTML generation.

Create a CSV file such as `edm-export/links.csv`:

```csv
image,url
slice_07.jpg,https://example.com/register
slice_12.jpg,https://example.com/event
footer_combined.jpg,https://www.nac.gov.sg/
```

Then wrap matching image tags with links. Use only image filenames in the `image` column, not full paths. Leave unlisted slices unlinked.

Use email-safe link markup:

```html
<a href="https://example.com/register" target="_blank" style="display:block; border:0; text-decoration:none;">
  <img src="images/slice_07.jpg" alt="">
</a>
```

Guidelines:

- Apply links after any manual footer grouping or combined-footer replacement, so regenerated HTML does not erase link edits.
- Do not add links by guessing from artwork text. Use a user-provided URL map or clearly labeled URLs in the brief.
- If one visual CTA spans multiple slices, either link every slice that forms the clickable area or combine those slices first when appropriate.
- Preserve image order, table structure, dimensions, and responsive CSS; only wrap the target `<img>` element.
- Avoid nesting anchors. If an image is already wrapped, update the existing `href` instead.

## Script

Use `scripts/build_edm_html.py` after slice JPEGs exist.

The script expects images in visual order and builds the Personalise-compatible fluid table structure described above. It can infer row type from source image widths at 2x:

- about `1320px` source width -> 1-column image
- about `660px` source width -> 2-column image
- about `440px` source width -> 3-column image

For preserved uneven footer rows, inspect exported image widths and adjust the generated HTML row manually if the script cannot infer the intended grouping.

Run:

```bash
python3 /Users/jim/.codex/skills/edm-ai/scripts/build_edm_html.py \
  --images-dir /path/to/edm-export/images \
  --output /path/to/edm-export/index.html \
  --bg '#F4F4F4'
```

Apply links:

```bash
python3 /Users/jim/.codex/skills/edm-ai/scripts/apply_edm_links.py \
  --html /path/to/edm-export/index.html \
  --links /path/to/edm-export/links.csv
```

If image names are not already in visual order, rename or pass files in sorted order using a temporary images folder. Do not guess a strange order if the exported sequence appears inconsistent; inspect dimensions and ask the user or derive order from slice `y`/`x`.

## Validation

Before finishing:

- Confirm `index.html` references the same number of images exported.
- Confirm no referenced images are missing.
- Run the Personalise compatibility double check below and fix any failure before reporting completion.
- Confirm split-column source widths are exact or close to 2x display widths:
  - 2-column display `330px` -> source `660px`
  - 3-column display `220px` -> source `440px`
- Confirm any preserved uneven footer rows keep their original slice proportions in HTML.
- If social icon PNGs were exported, confirm the PNG files exist, the HTML references them, and the replaced placeholder slice images are no longer referenced.
- If footer legal text was replaced, confirm the Terms of Use and Privacy Statement links appear, the placeholder slice images are no longer referenced, and the `320px` mobile CSS is present.
- If links were applied, confirm every linked image filename from `links.csv` appears in `index.html`, no anchors are nested, and unlisted slices remain unlinked.
- Report the output HTML path and image folder path.

### Personalise Compatibility Double Check

The final `index.html` must pass these checks before delivery:

- HTML shell contains `<center class="outer">`.
- HTML shell contains the MSO conditional wrapper `<!--[if mso]>` and an inner fixed-width table with `width="660" align="center"`.
- Main content table uses `class="container"`, `width="100%"`, and CSS/stylesheet support for `max-width: 660px`.
- Outer container cell includes `style="padding:0 16px;"` or an intentional user-specified equivalent.
- Every `<table>` has `cellpadding="0"`, `cellspacing="0"`, and `border="0"`.
- Every slice `<img>` has a fixed `width` attribute and inline CSS containing `display:block`, `width:100%`, `max-width`, `height:auto`, and `border:0`.
- Split-column tables use `width="50%"` for 2-column cells or `width="33.333%"` for 3-column cells, with `valign="top"` and zero font-size/line-height on cells.
- No `<title>` tag is present unless the user explicitly requested one.
