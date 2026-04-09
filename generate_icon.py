from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "presencecast-source.png"
PNG_PATH = ROOT / "presencecast.png"
ICO_PATH = ROOT / "presencecast.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Icon source image was not found at {SOURCE_PATH}")

    with Image.open(SOURCE_PATH) as source:
        rgba = source.convert("RGBA")
        rgba.save(PNG_PATH)
        rgba.save(ICO_PATH, format="ICO", sizes=[(size, size) for size in SIZES])


if __name__ == "__main__":
    main()
