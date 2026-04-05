#!/usr/bin/env python3
"""
Convert a PDF into a static GitHub Pages site by rasterizing each page to an image
and generating an index.html that displays the pages in order.

This is intentionally image-based so custom fonts, ligatures, and page layouts are
preserved exactly as rendered from the PDF.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pymupdf\nInstall with: pip install -r requirements.txt"
    ) from exc


@dataclass
class PageMeta:
    index: int
    image_path: str
    thumb_path: str
    width: int
    height: int
    label: str


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "pdf-site"


def safe_title_from_pdf(pdf_path: Path) -> str:
    return pdf_path.stem.replace("_", " ").replace("-", " ").strip() or "PDF Site"


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def render_page(
    page: fitz.Page,
    output_path: Path,
    thumb_path: Path,
    dpi: int,
    image_format: str,
    jpeg_quality: int,
    webp_quality: int,
    thumb_width: int,
) -> tuple[int, int]:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    thumb_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = image_format.lower()
    if fmt == "jpg":
        fmt = "jpeg"

    if fmt == "png":
        pix.save(str(output_path))
    elif fmt == "jpeg":
        pix.save(str(output_path), jpg_quality=jpeg_quality)
    elif fmt == "webp":
        pix.save(str(output_path), jpg_quality=webp_quality)
    else:
        raise ValueError(f"Unsupported image format: {image_format}")

    thumb_scale = thumb_width / max(pix.width, 1)
    thumb_matrix = fitz.Matrix(zoom * thumb_scale, zoom * thumb_scale)
    thumb_pix = page.get_pixmap(matrix=thumb_matrix, alpha=False)

    if fmt == "png":
        thumb_pix.save(str(thumb_path))
    elif fmt == "jpeg":
        thumb_pix.save(str(thumb_path), jpg_quality=jpeg_quality)
    elif fmt == "webp":
        thumb_pix.save(str(thumb_path), jpg_quality=min(webp_quality, 80))

    return pix.width, pix.height


def extract_outline(doc: fitz.Document) -> list[dict[str, Any]]:
    toc = doc.get_toc(simple=False)
    outline: list[dict[str, Any]] = []
    for item in toc:
        if len(item) < 3:
            continue
        level, title, page_no = item[:3]
        if not isinstance(page_no, int) or page_no < 1:
            continue
        outline.append({"level": int(level), "title": str(title), "page": int(page_no)})
    return outline


def build_html(title: str, pages: list[PageMeta], outline: list[dict[str, Any]], site_description: str) -> str:
    pages_json = json.dumps([asdict(page) for page in pages], ensure_ascii=False)
    outline_json = json.dumps(outline, ensure_ascii=False)
    title_escaped = html.escape(title)
    desc_escaped = html.escape(site_description)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title_escaped}</title>
  <meta name="description" content="{desc_escaped}" />
  <style>
    :root {{
      --bg: #0b1020;
      --text: #edf2ff;
      --muted: #9fb0db;
      --border: rgba(255,255,255,.12);
      --shadow: 0 12px 30px rgba(0,0,0,.28);
      --radius: 18px;
      --max-page-width: min(96vw, 1200px);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #08101f 0%, #0b1020 100%);
      color: var(--text);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{ display: grid; grid-template-columns: 320px minmax(0,1fr); min-height: 100vh; }}
    aside {{ position: sticky; top: 0; height: 100vh; overflow: auto; border-right: 1px solid var(--border); background: rgba(10,14,29,.92); padding: 20px; }}
    main {{ min-width: 0; padding: 24px; }}
    .brand, .page-card {{ border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }}
    .brand {{ margin-bottom: 18px; padding: 18px; background: rgba(255,255,255,.04); }}
    .brand h1 {{ margin: 0 0 8px; font-size: 1.25rem; }}
    .brand p {{ margin: 0; color: var(--muted); font-size: .95rem; }}
    .toolbar {{ display: grid; gap: 10px; margin-bottom: 18px; }}
    .search, .jump {{ width: 100%; border: 1px solid var(--border); background: rgba(255,255,255,.05); color: var(--text); border-radius: 14px; padding: 12px 14px; }}
    .section-title {{ margin: 18px 0 10px; color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }}
    .thumb-list, .outline, .pages {{ display: grid; gap: 10px; }}
    .thumb {{ display: grid; grid-template-columns: 72px minmax(0,1fr); gap: 12px; align-items: center; padding: 10px; border: 1px solid var(--border); border-radius: 14px; background: rgba(255,255,255,.04); }}
    .thumb img {{ width: 72px; display: block; border-radius: 8px; background: white; }}
    .thumb-sub, .footer {{ color: var(--muted); }}
    .outline a {{ display: block; padding: 8px 10px; border-radius: 10px; }}
    .page-card {{ width: var(--max-page-width); max-width: 100%; margin: 0 auto; padding: 14px; background: rgba(255,255,255,.04); scroll-margin-top: 24px; }}
    .page-top {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 10px; color: var(--muted); font-size: .95rem; }}
    .page-image {{ display: block; width: 100%; height: auto; border-radius: 18px; background: white; }}
    .empty {{ display: none; padding: 24px; text-align: center; color: var(--muted); border: 1px dashed var(--border); border-radius: 18px; background: rgba(255,255,255,.03); }}
    .footer {{ margin-top: 24px; text-align: center; font-size: .9rem; }}
    @media (max-width: 980px) {{
      .shell {{ grid-template-columns: 1fr; }}
      aside {{ position: relative; height: auto; border-right: 0; border-bottom: 1px solid var(--border); }}
      main {{ padding-top: 18px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>{title_escaped}</h1>
        <p>{desc_escaped}</p>
      </div>
      <div class="toolbar">
        <input id="search" class="search" type="search" placeholder="Filter pages or outline…" />
        <select id="jump" class="jump"><option value="">Jump to page…</option></select>
      </div>
      <div class="section-title">Outline</div>
      <nav id="outline" class="outline"></nav>
      <div class="section-title">Pages</div>
      <div id="thumbs" class="thumb-list"></div>
    </aside>
    <main>
      <div id="pages" class="pages"></div>
      <div id="empty" class="empty">No matching pages found.</div>
      <div class="footer">Generated from PDF as images for accurate font and layout preservation.</div>
    </main>
  </div>
  <script>
    const PAGES = {pages_json};
    const OUTLINE = {outline_json};
    const thumbsEl = document.getElementById('thumbs');
    const pagesEl = document.getElementById('pages');
    const outlineEl = document.getElementById('outline');
    const jumpEl = document.getElementById('jump');
    const searchEl = document.getElementById('search');
    const emptyEl = document.getElementById('empty');

    function createThumb(page) {{
      const a = document.createElement('a');
      a.href = `#page-${{page.index}}`;
      a.className = 'thumb';
      a.dataset.page = String(page.index);
      a.dataset.search = `page ${{page.index}} ${{page.label}}`.toLowerCase();
      a.innerHTML = `<img src="${{page.thumb_path}}" alt="Thumbnail for page ${{page.index}}" loading="lazy" /><div><div>${{page.label}}</div><div class="thumb-sub">${{page.width}} × ${{page.height}}</div></div>`;
      return a;
    }}

    function createPageCard(page) {{
      const section = document.createElement('section');
      section.className = 'page-card';
      section.id = `page-${{page.index}}`;
      section.dataset.search = `page ${{page.index}} ${{page.label}}`.toLowerCase();
      section.innerHTML = `<div class="page-top"><strong>${{page.label}}</strong><span>${{page.width}} × ${{page.height}}</span></div><img class="page-image" src="${{page.image_path}}" alt="${{page.label}}" loading="lazy" decoding="async" width="${{page.width}}" height="${{page.height}}" />`;
      return section;
    }}

    function createOutlineItem(item) {{
      const a = document.createElement('a');
      a.href = `#page-${{item.page}}`;
      a.textContent = item.title;
      a.style.paddingLeft = `${{Math.max(0, item.level - 1) * 16 + 10}}px`;
      a.dataset.search = `${{item.title}} page ${{item.page}}`.toLowerCase();
      return a;
    }}

    function populate() {{
      PAGES.forEach((page) => {{
        thumbsEl.appendChild(createThumb(page));
        pagesEl.appendChild(createPageCard(page));
        const option = document.createElement('option');
        option.value = `page-${{page.index}}`;
        option.textContent = page.label;
        jumpEl.appendChild(option);
      }});
      OUTLINE.forEach((item) => outlineEl.appendChild(createOutlineItem(item)));
      if (!OUTLINE.length) {{
        const fallback = document.createElement('div');
        fallback.style.color = 'var(--muted)';
        fallback.style.fontSize = '.95rem';
        fallback.textContent = 'No PDF outline found.';
        outlineEl.appendChild(fallback);
      }}
    }}

    function filterAll(query) {{
      const q = query.trim().toLowerCase();
      let visibleCount = 0;
      document.querySelectorAll('.thumb').forEach((el) => {{ el.style.display = (!q || el.dataset.search.includes(q)) ? '' : 'none'; }});
      document.querySelectorAll('.page-card').forEach((el) => {{
        const visible = !q || el.dataset.search.includes(q);
        el.style.display = visible ? '' : 'none';
        if (visible) visibleCount += 1;
      }});
      Array.from(outlineEl.children).forEach((el) => {{
        const search = el.dataset?.search || '';
        el.style.display = (!q || search.includes(q)) ? '' : 'none';
      }});
      emptyEl.style.display = visibleCount ? 'none' : 'block';
    }}

    searchEl.addEventListener('input', () => filterAll(searchEl.value));
    jumpEl.addEventListener('change', () => {{
      if (!jumpEl.value) return;
      const target = document.getElementById(jumpEl.value);
      if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});

    populate();
  </script>
</body>
</html>
"""


def build_readme(title: str, page_count: int) -> str:
    return f"# {title}\n\nGenerated from a PDF into a static site.\n\n- Total pages: {page_count}\n- Full-size images: assets/pages/\n- Thumbnails: assets/thumbs/\n"


def convert_pdf(
    pdf_path: Path,
    output_dir: Path,
    title: str | None,
    dpi: int,
    image_format: str,
    jpeg_quality: int,
    webp_quality: int,
    thumb_width: int,
) -> None:
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    resolved_title = title or safe_title_from_pdf(pdf_path)
    site_slug = slugify(resolved_title)
    site_description = "Image-rendered PDF viewer optimized for GitHub Pages. Pages are rasterized so custom fonts and exact layout are preserved."

    ensure_clean_dir(output_dir)
    pages_dir = output_dir / "assets" / "pages"
    thumbs_dir = output_dir / "assets" / "thumbs"
    pages_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    outline = extract_outline(doc)
    pages: list[PageMeta] = []

    ext = image_format.lower()
    if ext == "jpeg":
        ext = "jpg"

    try:
        for i, page in enumerate(doc, start=1):
            image_name = f"page-{i:04d}.{ext}"
            thumb_name = f"page-{i:04d}.{ext}"
            image_path = pages_dir / image_name
            thumb_path = thumbs_dir / thumb_name
            width, height = render_page(
                page=page,
                output_path=image_path,
                thumb_path=thumb_path,
                dpi=dpi,
                image_format=image_format,
                jpeg_quality=jpeg_quality,
                webp_quality=webp_quality,
                thumb_width=thumb_width,
            )
            pages.append(PageMeta(
                index=i,
                image_path=f"assets/pages/{image_name}",
                thumb_path=f"assets/thumbs/{thumb_name}",
                width=width,
                height=height,
                label=f"Page {i}",
            ))
    finally:
        doc.close()

    (output_dir / "index.html").write_text(build_html(resolved_title, pages, outline, site_description), encoding="utf-8")
    (output_dir / "README.md").write_text(build_readme(resolved_title, len(pages)), encoding="utf-8")
    (output_dir / "site.json").write_text(json.dumps({
        "title": resolved_title,
        "slug": site_slug,
        "source_pdf": pdf_path.name,
        "page_count": len(pages),
        "dpi": dpi,
        "image_format": image_format,
        "pages": [asdict(page) for page in pages],
        "outline": outline,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Generated GitHub Pages site in: {output_dir}")
    print(f"Pages: {len(pages)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a PDF into a GitHub Pages static site using page images.")
    parser.add_argument("pdf", type=Path, help="Path to the input PDF")
    parser.add_argument("--output", type=Path, default=Path("docs"), help="Output folder for the generated site")
    parser.add_argument("--title", type=str, default=None, help="Site title")
    parser.add_argument("--dpi", type=int, default=160, help="Render DPI for each page image")
    parser.add_argument("--image-format", choices=["png", "jpg", "jpeg", "webp"], default="webp")
    parser.add_argument("--jpeg-quality", type=int, default=88)
    parser.add_argument("--webp-quality", type=int, default=82)
    parser.add_argument("--thumb-width", type=int, default=220)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        convert_pdf(
            pdf_path=args.pdf,
            output_dir=args.output,
            title=args.title,
            dpi=args.dpi,
            image_format=args.image_format,
            jpeg_quality=args.jpeg_quality,
            webp_quality=args.webp_quality,
            thumb_width=args.thumb_width,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
