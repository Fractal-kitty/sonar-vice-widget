"""Generate application icon (.ico) for PyInstaller build."""

import os
from PIL import Image, ImageDraw


def generate_icon(output_path="assets/icon.ico"):
    """Create a SteelSeries-style orange icon in multiple sizes."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dark background circle
        draw.ellipse([1, 1, size - 1, size - 1], fill='#1C2333')

        # Orange outer ring
        ring_width = max(2, size // 10)
        draw.ellipse(
            [ring_width, ring_width, size - ring_width, size - ring_width],
            outline='#FF6600', width=ring_width,
        )

        # Inner orange filled dot
        inner = size // 4
        draw.ellipse([inner, inner, size - inner, size - inner], fill='#FF6600')

        images.append(img)

    # Save as .ico (multi-size)
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Icon saved: {output_path}")


if __name__ == "__main__":
    generate_icon()
