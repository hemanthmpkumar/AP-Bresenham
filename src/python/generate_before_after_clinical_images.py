"""
generate_before_after_clinical_images.py
========================================
Generates publication-quality Before-and-After clinical image panels comparing:
  1. Original Clinical Patient Slice (CT & MRI)
  2. BEFORE: Conventional Distributed Slab-Clip + Reseed Reconstruction (with streak artifacts)
  3. AFTER: 3D AP-Bresenham Distributed Reconstruction (clean, bit-exact continuation)
  4. ARTIFACT ERROR MAP: Residual difference (|Conv - AP|) revealing seam streaks
"""

import gzip
import struct
import math
import subprocess
from pathlib import Path

# Paths
ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "open_datasets"
FIG_DIR = ROOT / "paper" / "icccs2027_conference" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(Path(__file__).parent))
from ap_bresenham_3d import APBresenham3D, ground_truth_3d_clip, conventional_3d_clip_and_rasterize


def save_pgm_and_png(filename_base: Path, data_2d, width: int, height: int, colormap: str = "gray"):
    """Saves a 2D float array to PGM and converts to PNG using macOS sips."""
    flat = [data_2d[y][x] for y in range(height) for x in range(width)]
    min_v = min(flat)
    max_v = max(flat)
    rng = max_v - min_v if max_v > min_v else 1.0

    pgm_path = filename_base.with_suffix(".pgm")
    png_path = filename_base.with_suffix(".png")

    if colormap == "gray":
        pixels = bytes([int(min(255, max(0, (v - min_v) / rng * 255.0))) for v in flat])
        with open(pgm_path, "wb") as f:
            f.write(f"P5\n{width} {height}\n255\n".encode("ascii"))
            f.write(pixels)
    elif colormap == "hot":  # for difference artifact maps (black -> red -> yellow -> white)
        ppm_path = filename_base.with_suffix(".ppm")
        rgb_bytes = bytearray()
        for v in flat:
            norm = min(1.0, max(0.0, (v - min_v) / rng))
            # Heat colormap
            if norm < 0.33:
                r = int(norm / 0.33 * 255.0)
                g = 0
                b = 0
            elif norm < 0.66:
                r = 255
                g = int((norm - 0.33) / 0.33 * 255.0)
                b = 0
            else:
                r = 255
                g = 255
                b = int((norm - 0.66) / 0.34 * 255.0)
            rgb_bytes.extend([r, g, b])
        with open(ppm_path, "wb") as f:
            f.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
            f.write(rgb_bytes)
        subprocess.run(["sips", "-s", "format", "png", str(ppm_path), "--out", str(png_path)], capture_output=True)
        ppm_path.unlink(missing_ok=True)
        return png_path

    subprocess.run(["sips", "-s", "format", "png", str(pgm_path), "--out", str(png_path)], capture_output=True)
    pgm_path.unlink(missing_ok=True)
    return png_path


def process_clinical_volume(is_ct: bool, N: int = 64, n_angles: int = 180, n_detectors: int = 64):
    prefix = "ct" if is_ct else "mri"
    print(f"--> Processing clinical {'Abdominal CT' if is_ct else 'Brain MRI'} volume...")

    if is_ct:
        nii_path = DATA_DIR / "CT_Abdo.nii.gz"
        with gzip.open(nii_path, "rb") as f:
            hdr = f.read(348)
            vox_offset = int(struct.unpack("<f", hdr[108:112])[0])
            f.seek(vox_offset)
            raw = f.read()
        nx, ny, nz = 255, 178, 256
        cx, cy, cz = 128, 89, 120
        half = N // 2
        grid = [[0.0 for _ in range(N)] for _ in range(N)]
        for y in range(N):
            gy = cy - half + y
            for x in range(N):
                gx = cx - half + x
                if 0 <= gx < nx and 0 <= gy < ny:
                    idx = (gx + gy * nx + cz * nx * ny) * 2
                    val = struct.unpack("<h", raw[idx:idx+2])[0]
                    # Hounsfield Unit attenuation
                    grid[y][x] = max(0.0, (val + 1000.0) / 1000.0 * 0.2)
    else:
        nii_path = DATA_DIR / "mni152.nii.gz"
        with gzip.open(nii_path, "rb") as f:
            hdr = f.read(348)
            vox_offset = int(struct.unpack("<f", hdr[108:112])[0])
            f.seek(vox_offset)
            raw = f.read()
        nx, ny, nz = 207, 256, 215
        cx, cy, cz = 103, 128, 100
        half = N // 2
        grid = [[0.0 for _ in range(N)] for _ in range(N)]
        for y in range(N):
            gy = cy - half + y
            for x in range(N):
                gx = cx - half + x
                if 0 <= gx < nx and 0 <= gy < ny:
                    idx = gx + gy * nx + cz * nx * ny
                    grid[y][x] = float(raw[idx]) / 255.0

    # Save original reference slice
    orig_png = save_pgm_and_png(FIG_DIR / f"{prefix}_orig", grid, N, N)

    # 4 Sub-volume domain decomposition (2x2 partition seams at x=31|32 and y=31|32)
    chunks = [
        (0, 31, 0, 31, 0, 0),
        (32, 63, 0, 31, 0, 0),
        (0, 31, 32, 63, 0, 0),
        (32, 63, 32, 63, 0, 0)
    ]

    r = N * 0.45
    center = N / 2.0

    sino_conv = [[0.0 for _ in range(n_detectors)] for _ in range(n_angles)]
    sino_ap = [[0.0 for _ in range(n_detectors)] for _ in range(n_angles)]

    for a in range(n_angles):
        theta = math.pi * a / n_angles
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        for d in range(n_detectors):
            offset = (d - n_detectors / 2.0 + 0.5) * (N / n_detectors)
            x0 = int(round(center - r * sin_t + offset * cos_t))
            y0 = int(round(center + r * cos_t + offset * sin_t))
            x1 = int(round(center + r * sin_t + offset * cos_t))
            y1 = int(round(center - r * cos_t + offset * sin_t))

            x0, y0 = max(0, min(N-1, x0)), max(0, min(N-1, y0))
            x1, y1 = max(0, min(N-1, x1)), max(0, min(N-1, y1))

            # Conventional
            c_vox = []
            for ch in chunks:
                c_vox.extend(conventional_3d_clip_and_rasterize(x0, y0, 0, x1, y1, 0, *ch))
            sino_conv[a][d] = sum(grid[y][x] for (x, y, z) in c_vox)

            # AP-Bresenham
            ap_vox = []
            for ch in chunks:
                ap_vox.extend(APBresenham3D.clip_and_rasterize(x0, y0, 0, x1, y1, 0, *ch))
            sino_ap[a][d] = sum(grid[y][x] for (x, y, z) in ap_vox)

    # Back-projection reconstruction
    recon_conv = [[0.0 for _ in range(N)] for _ in range(N)]
    recon_ap = [[0.0 for _ in range(N)] for _ in range(N)]

    for a in range(n_angles):
        theta = math.pi * a / n_angles
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        for y in range(N):
            dy = y - center + 0.5
            for x in range(N):
                dx = x - center + 0.5
                t = -dx * sin_t + dy * cos_t
                d_idx = int(round((t / (N / n_detectors)) + n_detectors / 2.0 - 0.5))
                if 0 <= d_idx < n_detectors:
                    recon_conv[y][x] += sino_conv[a][d_idx]
                    recon_ap[y][x] += sino_ap[a][d_idx]

    diff_recon = [[abs(recon_conv[y][x] - recon_ap[y][x]) for x in range(N)] for y in range(N)]

    before_png = save_pgm_and_png(FIG_DIR / f"{prefix}_before", recon_conv, N, N)
    after_png = save_pgm_and_png(FIG_DIR / f"{prefix}_after", recon_ap, N, N)
    diff_png = save_pgm_and_png(FIG_DIR / f"{prefix}_diff", diff_recon, N, N, colormap="hot")

    print(f"  ✓ {prefix.upper()} panels generated successfully: orig, before, after, diff")


if __name__ == "__main__":
    process_clinical_volume(is_ct=True)
    process_clinical_volume(is_ct=False)

