import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = Path(r"C:\Users\conno\Downloads\Copilot_20260408_233225.png")
WORKSPACE_SOURCE = ROOT / "presencecast-source.png"
PNG_PATH = ROOT / "presencecast.png"
ICO_PATH = ROOT / "presencecast.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]


def pack_ico(images: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(images))
    directory = bytearray()
    payload = bytearray()
    offset = 6 + (16 * len(images))

    for size, png_bytes in images:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(png_bytes),
                offset,
            )
        )
        payload.extend(png_bytes)
        offset += len(png_bytes)

    return header + directory + payload


def main() -> None:
    source = WORKSPACE_SOURCE if WORKSPACE_SOURCE.exists() else SOURCE_PATH
    if not source.exists():
        raise FileNotFoundError(
            f"Icon source image was not found at {WORKSPACE_SOURCE} or {SOURCE_PATH}"
        )

    if source != WORKSPACE_SOURCE:
        shutil.copyfile(source, WORKSPACE_SOURCE)

    shutil.copyfile(source, PNG_PATH)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        temp_outputs = [tmp_path / f"icon-{size}.png" for size in SIZES]
        joined_outputs = ",".join(str(path) for path in temp_outputs)

        powershell_script = rf"""
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$src = '{source}'
$outputs = '{joined_outputs}'.Split(',')
$sizes = @(16,24,32,48,64,128,256)
$image = [System.Drawing.Image]::FromFile($src)
for ($i = 0; $i -lt $sizes.Length; $i++) {{
    $size = $sizes[$i]
    $bitmap = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.DrawImage($image, 0, 0, $size, $size)
    $bitmap.Save($outputs[$i], [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}}
$image.Dispose()
"""

        subprocess.run(
            ["powershell", "-NoProfile", "-Command", powershell_script],
            check=True,
        )

        ico_bytes = pack_ico([(size, path.read_bytes()) for size, path in zip(SIZES, temp_outputs)])
        ICO_PATH.write_bytes(ico_bytes)


if __name__ == "__main__":
    main()
