"""Generate application icon (.icns for macOS, .ico for Windows)."""

import os
import platform
import subprocess
import shutil
import tempfile
from PIL import Image, ImageDraw

IS_MACOS = platform.system() == "Darwin"


def _create_icon_images():
    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    images = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([1, 1, size - 1, size - 1], fill='#1C2333')
        ring_width = max(2, size // 10)
        draw.ellipse([ring_width, ring_width, size - ring_width, size - ring_width],
                     outline='#FF6600', width=ring_width)
        inner = size // 4
        draw.ellipse([inner, inner, size - inner, size - inner], fill='#FF6600')
        images.append(img)
    return images, sizes


def generate_ico(output_path="assets/icon.ico"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    images, sizes = _create_icon_images()
    ico_images = [img for img, s in zip(images, sizes) if s <= 256]
    ico_sizes = [s for s in sizes if s <= 256]
    ico_images[0].save(output_path, format='ICO',
                       sizes=[(s, s) for s in ico_sizes], append_images=ico_images[1:])
    print(f"Icon saved: {output_path}")


def generate_icns(output_path="assets/icon.icns"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    images, sizes = _create_icon_images()

    if not IS_MACOS:
        png_path = output_path.replace(".icns", ".png")
        images[-1].save(png_path)
        print(f"PNG icon saved: {png_path} (convert to .icns on macOS)")
        return

    # Use iconutil on macOS
    iconset_dir = tempfile.mkdtemp(suffix=".iconset")
    try:
        mapping = {
            16: ["icon_16x16.png"],
            32: ["icon_16x16@2x.png", "icon_32x32.png"],
            64: ["icon_32x32@2x.png"],
            128: ["icon_128x128.png"],
            256: ["icon_128x128@2x.png", "icon_256x256.png"],
            512: ["icon_256x256@2x.png", "icon_512x512.png"],
            1024: ["icon_512x512@2x.png"],
        }
        for img, size in zip(images, sizes):
            for filename in mapping.get(size, []):
                img.save(os.path.join(iconset_dir, filename))

        subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", output_path], check=True)
        print(f"Icon saved: {output_path}")
    except Exception as e:
        print(f"iconutil failed: {e}, saving as PNG fallback")
        images[-1].save(output_path.replace(".icns", ".png"))
    finally:
        shutil.rmtree(iconset_dir, ignore_errors=True)


def generate_icon():
    if IS_MACOS:
        generate_icns("assets/icon.icns")
    generate_ico("assets/icon.ico")


if __name__ == "__main__":
    generate_icon()
