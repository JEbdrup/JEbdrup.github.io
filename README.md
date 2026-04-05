# PDF to GitHub Pages

Convert a PDF into a static GitHub Pages site by rasterizing every page to an image.

This is the right approach when your PDF uses custom fonts, exact typography, or fixed page composition that must look the same on the web.

## What this project does

- renders each PDF page to an image
- creates thumbnails for sidebar navigation
- generates a static `docs/` site
- publishes cleanly to GitHub Pages
- preserves visual fidelity better than reflowing HTML conversion

## Best use cases

- brochures
- proposals
- reports
- presentations
- portfolios
- brand-sensitive documents
- PDFs with custom fonts or exact layout

## What to do
1. Remove the <NAME>.pdf file from root directory.
2. Put in another <NAME>.pdf file
3. Push to git, and let GitHub action do the build and deployment