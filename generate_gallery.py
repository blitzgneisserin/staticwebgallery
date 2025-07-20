import os
import subprocess
import json
import shutil
from collections import defaultdict
from slugify import slugify
from jinja2 import Environment, FileSystemLoader

# Directories
IMAGES_DIR = "images"
OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"

# Define metadata fields
METADATA_FIELDS = {
    "City": "City",
    "State": "Province-State",
    "Date": "DateTimeOriginal"
}

# Prepare Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
env.filters['slugify'] = slugify  # Make the slugify filter available in templates

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_metadata(filepath):
    """Reads defined metadata and keywords using exiftool."""
    result = subprocess.run(
        ["exiftool", "-j", filepath],
        capture_output=True,
        text=True
    )
    data = json.loads(result.stdout)[0]

    # Collect metadata
    metadata = {
        key: data.get(field)
        for key, field in METADATA_FIELDS.items()
        if data.get(field)
    }

    # Extract keywords
    keywords = data.get("Keywords")
    if isinstance(keywords, str):
        keywords = [keywords]
    elif isinstance(keywords, list):
        keywords = [str(k) for k in keywords if k is not None]
    else:
        keywords = []

    return metadata, keywords


def collect_images():
    """Scans the images directory, reads metadata, and groups by tags."""
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
    """Generates the index page with links to all tags."""
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
    """Generates HTML pages per tag with thumbnail previews."""
    template = env.get_template("tag.html")
    for tag, images in tag_to_images.items():
        tag_str = str(tag)
        slug = slugify(tag_str)
        html = template.render(tag=tag_str, images=images)
        output_file = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)


def render_image_pages_per_tag(tag_to_images):
    """Generates individual image pages with navigation within each tag."""
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
    """Copies all images into the output/images folder."""
    output_images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(output_images_dir, exist_ok=True)

    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            src = os.path.join(IMAGES_DIR, filename)
            dst = os.path.join(output_images_dir, filename)
            shutil.copy2(src, dst)


def generate_thumbnails():
    """Generates square thumbnails (300x300) from images in the images directory using ImageMagick."""
    thumbs_dir = os.path.join(OUTPUT_DIR, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)

    for filename in os.listdir(IMAGES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        input_path = os.path.join(IMAGES_DIR, filename)
        output_path = os.path.join(thumbs_dir, filename)

        # ImageMagick command: first resize the smaller side to 300, then crop to 300x300 centered
        cmd = [
            "convert",
            input_path,
            "-resize", "300x300^",     # Scale so that the shortest side is 300 and the other is >= 300
            "-gravity", "center",      # Center the cropping area
            "-extent", "300x300",      # Crop exactly to 300x300
            "-quality", "67",          # Set output quality to 67%
            output_path
        ]

        subprocess.run(cmd, check=True)


def main():
    tag_to_images = collect_images()
    render_index_page(tag_to_images)
    render_tag_pages(tag_to_images)
    render_image_pages_per_tag(tag_to_images)
    copy_images()
    generate_thumbnails()
    print("Gallery successfully generated.")


if __name__ == "__main__":
    main()
