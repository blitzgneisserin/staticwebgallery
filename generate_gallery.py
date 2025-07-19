import os
import subprocess
import json
import shutil
from collections import defaultdict
from slugify import slugify
from jinja2 import Environment, FileSystemLoader

# Verzeichnisse
IMAGES_DIR = "images"
OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"

# Metadatenfelder definieren
METADATA_FIELDS = {
    "City": "City",
    "State": "Province-State",
    "Date": "DateTimeOriginal"
}

# Jinja2-Umgebung vorbereiten
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
env.filters['slugify'] = slugify  # slugify-Filter für Templates verfügbar machen

# Sicherstellen, dass das Ausgabeverzeichnis existiert
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_metadata(filepath):
    """Liest definierte Metadaten und Keywords mit exiftool aus."""
    result = subprocess.run(
        ["exiftool", "-j", filepath],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)[0]

    # Metadaten sammeln
    metadata = {
        key: data.get(field)
        for key, field in METADATA_FIELDS.items()
        if data.get(field)
    }

    # Keywords auslesen
    keywords = data.get("Keywords")
    if isinstance(keywords, str):
        keywords = [keywords]
    elif isinstance(keywords, list):
        keywords = [str(k) for k in keywords if k is not None]
    else:
        keywords = []

    return metadata, keywords


def collect_images():
    """Durchsucht das Image-Verzeichnis, liest Metadaten und gruppiert nach Tags."""
    tag_to_images = defaultdict(list)

    for filename in sorted(os.listdir(IMAGES_DIR)):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        filepath = os.path.join(IMAGES_DIR, filename)
        metadata, keywords = get_metadata(filepath)
        slug = slugify(os.path.splitext(filename)[0])

        image_data = {
            "filename": filename,
            "slug": slug,
            "metadata": metadata
        }

        for keyword in keywords:
            tag_to_images[str(keyword)].append(image_data)

    return tag_to_images


def render_index_page(tag_to_images):
    """Erzeugt die Startseite mit Links zu allen Tags."""
    template = env.get_template("index.html")
    tags = [
        {
            "label": tag,
            "slug": slugify(tag),
            "count": len(images)
        }
        for tag, images in sorted(tag_to_images.items())
    ]
    html = template.render(tags=tags)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def render_tag_pages(tag_to_images):
    """Erzeugt HTML-Seiten pro Tag mit Vorschaubildern."""
    template = env.get_template("tag.html")
    for tag, images in tag_to_images.items():
        tag_str = str(tag)
        slug = slugify(tag_str)
        html = template.render(tag=tag_str, images=images)
        output_file = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)


def render_image_pages_per_tag(tag_to_images):
    """Erzeugt Bildseiten mit Navigation innerhalb jedes Tags."""
    template = env.get_template("image.html")

    for tag, images in tag_to_images.items():
        tag_slug = slugify(tag)
        total = len(images)

        for index, img in enumerate(images):
            filename = img["filename"]
            metadata = img["metadata"]
            slug = img["slug"]

            prev_slug = images[index - 1]["slug"] if index > 0 else None
            next_slug = images[index + 1]["slug"] if index < total - 1 else None

            html = template.render(
                filename=filename,
                metadata=metadata,
                prev_slug=prev_slug,
                next_slug=next_slug,
                tag_slug=tag_slug
            )

            output_file = os.path.join(OUTPUT_DIR, f"{slug}-{tag_slug}.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)


def copy_images():
    """Kopiert alle Bilder in den output/images-Ordner."""
    output_images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(output_images_dir, exist_ok=True)

    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            src = os.path.join(IMAGES_DIR, filename)
            dst = os.path.join(output_images_dir, filename)
            shutil.copy2(src, dst)


def main():
    tag_to_images = collect_images()
    render_index_page(tag_to_images)
    render_tag_pages(tag_to_images)
    render_image_pages_per_tag(tag_to_images)
    copy_images()
    print("Galerie erfolgreich generiert.")


if __name__ == "__main__":
    main()
