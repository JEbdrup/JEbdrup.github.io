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

## Requirements

- Ubuntu on WSL
- Python 3.10+
- Git

Install system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

Check Python:

```bash
python3 --version
```

## Project files

```text
.github/
  workflows/
    build-pages.yml
build.sh
cleanup.sh
pdf_to_github_pages.py
requirements.txt
README.md
your-file.pdf
```

## Quick start

Make the scripts executable:

```bash
chmod +x build.sh cleanup.sh
```

Build a site from a PDF:

```bash
./build.sh ./your-file.pdf --title "My PDF Site"
```

Output is written to:

```text
docs/
```

## Best quality settings

For the best-looking GitHub Pages site, start with these rules:

### Option 1: Balanced quality and file size

Best default for most PDFs:

```bash
./build.sh ./your-file.pdf \
  --title "My PDF Site" \
  --dpi 200 \
  --image-format webp \
  --webp-quality 90 \
  --thumb-width 260
```

Use this when:
- the PDF contains mixed text and images
- you want a good balance of sharpness and speed
- the document is more than a few pages long

### Option 2: Maximum visual fidelity

Best quality, but larger output:

```bash
./build.sh ./your-file.pdf \
  --title "My PDF Site" \
  --dpi 240 \
  --image-format png \
  --thumb-width 300
```

Use this when:
- typography must be extremely crisp
- the PDF has fine linework or diagrams
- file size matters less than appearance

### Option 3: Smaller site for large PDFs

Good for long documents:

```bash
./build.sh ./your-file.pdf \
  --title "My PDF Site" \
  --dpi 160 \
  --image-format webp \
  --webp-quality 78 \
  --thumb-width 220
```

Use this when:
- the PDF has many pages
- you want faster loading
- mobile performance matters more than perfect sharpness

## Recommended quality workflow

1. Start with `webp`, `dpi 200`, and `webp-quality 90`
2. Open the generated `docs/index.html` locally
3. Check small text, thin lines, and images
4. If text looks soft, increase to `--dpi 220` or `--dpi 240`
5. If the site becomes too large, lower `--webp-quality` to `85` or `80`
6. If fidelity still is not enough, switch to `--image-format png`

## Step-by-step example: PDF to GitHub Pages site

This example shows the full workflow from PDF to published site.

### 1. Create a new project folder

```bash
mkdir author-pdf-site
cd author-pdf-site
```

### 2. Add the project files

Put these files in the folder:

```text
build.sh
cleanup.sh
pdf_to_github_pages.py
requirements.txt
README.md
.github/workflows/build-pages.yml
```

Then copy your PDF into the same folder, for example:

```text
brand-book.pdf
```

### 3. Make the scripts executable

```bash
chmod +x build.sh cleanup.sh
```

### 4. Build locally with high quality settings

```bash
./build.sh ./brand-book.pdf \
  --title "Brand Book" \
  --dpi 200 \
  --image-format webp \
  --webp-quality 90 \
  --thumb-width 260
```

### 5. Review the generated site locally

Open the main HTML file from WSL.

From Windows Explorer, you can browse to the folder and open:

```text
docs/index.html
```

Or from WSL, print the path:

```bash
pwd
```

Then open the folder in Windows and inspect the generated site.

### 6. Initialize Git

```bash
git init
git add .
git commit -m "Initial PDF site"
```

### 7. Create a GitHub repository and push

Example:

```bash
git branch -M main
git remote add origin git@github.com:YOUR-USER/author-pdf-site.git
git push -u origin main
```

### 8. Enable GitHub Pages

In GitHub:

1. Open **Settings**
2. Open **Pages**
3. Set **Source** to **GitHub Actions**

### 9. Let the workflow publish the site

When the push reaches GitHub, the workflow will:
- install Python
- install project dependencies
- find the PDF in the repo root
- build the `docs/` site
- deploy it to GitHub Pages

### 10. Update the site later

Replace the PDF or edit the existing PDF, then rebuild and push again:

```bash
./build.sh ./brand-book.pdf --title "Brand Book" --dpi 200 --image-format webp --webp-quality 90
git add .
git commit -m "Update PDF site"
git push
```

## Local manual run

If you want to run the Python script directly:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python pdf_to_github_pages.py ./your-file.pdf --output docs --title "My PDF Site"
```

## Cleanup

Remove the virtual environment, docs output, and Python cache:

```bash
./cleanup.sh --all
```

Examples:

```bash
./cleanup.sh --venv
./cleanup.sh --docs
./cleanup.sh --cache
```

## Troubleshooting

### `python3: command not found`

Install Python:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### `No module named fitz`

Reinstall dependencies:

```bash
./cleanup.sh --all
./build.sh ./your-file.pdf --title "My PDF Site"
```

### The text looks soft

Try:

```bash
./build.sh ./your-file.pdf --dpi 220 --image-format webp --webp-quality 92
```

Or switch to PNG:

```bash
./build.sh ./your-file.pdf --dpi 240 --image-format png
```

### The site is too large

Lower the settings:

```bash
./build.sh ./your-file.pdf --dpi 160 --image-format webp --webp-quality 78
```

## Publish model

This project supports two publishing styles:

1. local build into `docs/`
2. GitHub Actions build and deploy to GitHub Pages

For most use cases, the GitHub Actions deployment is the better long-term option.
