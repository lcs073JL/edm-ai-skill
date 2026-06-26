#!/usr/bin/env python3
import argparse
from html import escape
import os
from pathlib import Path
import struct


def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read(2)
        if data != b"\xff\xd8":
            raise ValueError(f"{path} is not a JPEG")
        while True:
            marker_start = f.read(1)
            if not marker_start:
                raise ValueError(f"Could not find JPEG size in {path}")
            if marker_start != b"\xff":
                continue
            marker = f.read(1)
            while marker == b"\xff":
                marker = f.read(1)
            if marker in [b"\xd8", b"\xd9"]:
                continue
            length_bytes = f.read(2)
            if len(length_bytes) != 2:
                raise ValueError(f"Invalid JPEG segment in {path}")
            length = struct.unpack(">H", length_bytes)[0]
            if marker[0] in list(range(0xC0, 0xC4)) + list(range(0xC5, 0xC8)) + list(range(0xC9, 0xCC)) + list(range(0xCD, 0xD0)):
                precision = f.read(1)
                height, width = struct.unpack(">HH", f.read(4))
                return width, height
            f.seek(length - 2, 1)


def column_span(width):
    if width >= 1000:
        return 1
    if width >= 560:
        return 2
    return 3


def group_images(images):
    rows = []
    i = 0
    while i < len(images):
        span = column_span(images[i]["width"])
        count = span
        row = images[i : i + count]
        if len(row) != count:
            raise ValueError("Image sequence ends mid-row")
        rows.append(row)
        i += count
    return rows


def image_src(file, output_parent):
    rel = os.path.relpath(file, output_parent)
    if rel.startswith(".."):
        return str(file)
    return rel


def src_exists(src, output_parent):
    path = Path(src)
    if path.is_absolute():
        return path.exists()
    return (output_parent / src).exists()


def img_tag(image, display_width):
    src = escape(image["src"])
    return (
        f'<img src="{src}" width="{display_width}" alt="" '
        f'style="display:block; width:100%; max-width:{display_width}px; height:auto; '
        'border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic;">'
    )


def render_row(row):
    if len(row) == 1:
        return f"""          <tr>
            <td style="font-size:0; line-height:0; padding:0; margin:0;">
              {img_tag(row[0], 660)}
            </td>
          </tr>"""
    if len(row) == 2:
        cells = "\n".join(
            f"""                  <td class="col-2" width="50%" valign="top" style="font-size:0; line-height:0; padding:0; margin:0;">
                    {img_tag(image, 330)}
                  </td>"""
            for image in row
        )
        return f"""          <tr>
            <td style="font-size:0; line-height:0; padding:0; margin:0;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt;">
                <tr>
{cells}
                </tr>
              </table>
            </td>
          </tr>"""
    if len(row) == 3:
        cells = "\n".join(
            f"""                  <td class="col-3" width="33.333%" valign="top" style="font-size:0; line-height:0; padding:0; margin:0;">
                    {img_tag(image, 220)}
                  </td>"""
            for image in row
        )
        return f"""          <tr>
            <td style="font-size:0; line-height:0; padding:0; margin:0;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt;">
                <tr>
{cells}
                </tr>
              </table>
            </td>
          </tr>"""
    raise ValueError(f"Unsupported row with {len(row)} images")


def build_html(rows, bg, title):
    body_rows = "\n".join(render_row(row) for row in rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="x-apple-disable-message-reformatting">
  <style>
    body, table, td, p, a {{
      margin: 0;
      padding: 0;
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}

    table {{
      border-collapse: collapse;
      mso-table-lspace: 0pt;
      mso-table-rspace: 0pt;
    }}

    img {{
      border: 0;
      outline: none;
      text-decoration: none;
      -ms-interpolation-mode: bicubic;
      display: block;
      height: auto;
      line-height: 100%;
    }}

    body {{
      width: 100% !important;
      min-width: 100%;
      background-color: {bg};
    }}

    .outer {{
      width: 100%;
      background-color: {bg};
    }}

    .container {{
      width: 100%;
      max-width: 660px;
      background-color: #ffffff;
    }}

    .col-2,
    .col-3 {{
      font-size: 0;
      line-height: 0;
    }}

    @media only screen and (max-width: 480px) {{
      body, table, td, p, a, li, blockquote {{
        -webkit-text-size-adjust: none !important;
      }}
    }}
  </style>
</head>
<body>
  <center class="outer">
    <table role="presentation" width="100%" class="outer" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td align="center" style="padding:0 16px;">
          <!--[if mso]>
          <table role="presentation" width="660" align="center" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
          <![endif]-->

          <table role="presentation" width="100%" class="container" cellpadding="0" cellspacing="0" border="0">
{body_rows}
          </table>

          <!--[if mso]>
              </td>
            </tr>
          </table>
          <![endif]-->
        </td>
      </tr>
    </table>
  </center>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Build responsive EDM HTML from 2x JPEG slices.")
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bg", default="#F4F4F4")
    parser.add_argument("--title", default="EDM")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    output = Path(args.output)
    files = sorted(images_dir.glob("*.jpg"))
    if not files:
        raise SystemExit(f"No .jpg files found in {images_dir}")

    images = []
    for file in files:
        width, height = jpeg_size(file)
        images.append({
            "path": file,
            "src": image_src(file, output.parent),
            "width": width,
            "height": height,
        })

    rows = group_images(images)
    output.write_text(build_html(rows, args.bg, args.title), encoding="utf-8")
    missing = [image["src"] for image in images if not src_exists(image["src"], output.parent)]
    print(f"Wrote {output}")
    print(f"Images: {len(images)}")
    print(f"Rows: {len(rows)}")
    if missing:
        raise SystemExit(f"Missing referenced images: {missing}")


if __name__ == "__main__":
    main()
