#!/usr/bin/env python3
import argparse
import csv
from html import escape
from html.parser import HTMLParser
from pathlib import Path


class ImgLinker(HTMLParser):
    def __init__(self, links):
        super().__init__(convert_charrefs=False)
        self.links = links
        self.out = []
        self.anchor_depth = 0
        self.applied = set()

    def attrs_text(self, attrs):
        return ''.join(f' {name}="{escape(value or "", quote=True)}"' for name, value in attrs)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.anchor_depth += 1
        if tag.lower() == 'img':
            attrs_dict = dict(attrs)
            src = attrs_dict.get('src', '')
            filename = Path(src).name
            url = self.links.get(filename)
            if url and self.anchor_depth == 0:
                self.out.append(f'<a href="{escape(url, quote=True)}" target="_blank" style="display:block; border:0; text-decoration:none;">')
                self.out.append(f'<img{self.attrs_text(attrs)}>')
                self.out.append('</a>')
                self.applied.add(filename)
                return
        self.out.append(f'<{tag}{self.attrs_text(attrs)}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() != 'img':
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.out.append(f'</{tag}>')
        if tag.lower() == 'a' and self.anchor_depth:
            self.anchor_depth -= 1

    def handle_data(self, data):
        self.out.append(data)

    def handle_entityref(self, name):
        self.out.append(f'&{name};')

    def handle_charref(self, name):
        self.out.append(f'&#{name};')

    def handle_comment(self, data):
        self.out.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self.out.append(f'<!{decl}>')


parser = argparse.ArgumentParser(description='Wrap selected EDM slice images with links from a CSV map.')
parser.add_argument('--html', required=True, help='Path to index.html')
parser.add_argument('--links', required=True, help='CSV with image,url columns')
args = parser.parse_args()

html_path = Path(args.html)
links_path = Path(args.links)

links = {}
with links_path.open(newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames or 'image' not in reader.fieldnames or 'url' not in reader.fieldnames:
        raise SystemExit('links.csv must have image,url columns')
    for row in reader:
        image = (row.get('image') or '').strip()
        url = (row.get('url') or '').strip()
        if image and url:
            links[Path(image).name] = url

linker = ImgLinker(links)
linker.feed(html_path.read_text(encoding='utf-8'))
html_path.write_text(''.join(linker.out), encoding='utf-8')

missing = sorted(set(links) - linker.applied)
print(f'Applied links: {len(linker.applied)}')
if missing:
    raise SystemExit(f'Images from links.csv not found or already linked: {missing}')
