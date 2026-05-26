"""
post_process.py
───────────────
Post-process the GEE-exported LULC GeoTIFF:
  • Compute per-class area statistics
  • Plot a colour-classified map
  • Generate a confusion-matrix heatmap  (if ground-truth CSV available)
  • Save publication-ready figures to results/figures/

Requirements:  pip install rasterio numpy matplotlib pandas seaborn geopandas
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from pathlib import Path

try:
    import rasterio
    from rasterio.plot import show as rio_show
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("[warn] rasterio not found – skipping raster operations")

try:
    import seaborn as sns
    HAS_SNS = True
except ImportError:
    HAS_SNS = False

# ── CONFIG ───────────────────────────────────────────────────
LULC_RASTER   = Path("results/lulc_2023.tif")          # GEE export
CONFUSION_CSV = Path("results/confusion_matrix.csv")    # optional
OUT_DIR       = Path("results/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_INFO = {
    0: ("Water",           "#1a6faf"),
    1: ("Forest",          "#228b22"),
    2: ("Cropland",        "#f5c518"),
    3: ("Urban / Built-up","#e74c3c"),
    4: ("Grassland",       "#90ee90"),
}

# ── 1. AREA STATISTICS ───────────────────────────────────────
def compute_area_stats(arr: np.ndarray, pixel_area_ha: float = 1.0) -> pd.DataFrame:
    rows = []
    for cls, (name, _) in CLASS_INFO.items():
        count = int(np.sum(arr == cls))
        rows.append({"Class": cls, "Name": name,
                     "Pixels": count,
                     "Area_ha": round(count * pixel_area_ha, 2),
                     "Pct": 0.0})
    df = pd.DataFrame(rows)
    df["Pct"] = (df["Area_ha"] / df["Area_ha"].sum() * 100).round(2)
    return df


def plot_area_bar(df: pd.DataFrame):
    colours = [CLASS_INFO[c][1] for c in df["Class"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(df["Name"], df["Area_ha"], color=colours, edgecolor="white", linewidth=0.8)
    for bar, pct in zip(bars, df["Pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_title("Land Use / Land Cover — Area Statistics (2023)", fontsize=13, pad=14)
    ax.set_ylabel("Area (ha)")
    ax.set_xlabel("Class")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    out = OUT_DIR / "area_statistics.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[✓] Saved {out}")


# ── 2. CLASSIFIED MAP ────────────────────────────────────────
def plot_classified_map(arr: np.ndarray):
    cmap   = mcolors.ListedColormap([CLASS_INFO[i][1] for i in range(5)])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm   = mcolors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(arr, cmap=cmap, norm=norm, interpolation="nearest")
    patches = [mpatches.Patch(color=CLASS_INFO[i][1], label=CLASS_INFO[i][0])
               for i in range(5)]
    ax.legend(handles=patches, loc="lower right", fontsize=9, framealpha=0.85)
    ax.set_title("Land Use / Land Cover Classification — Lake Victoria Basin (2023)",
                 fontsize=12, pad=12)
    ax.axis("off")
    plt.tight_layout()
    out = OUT_DIR / "lulc_map.png"
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[✓] Saved {out}")


# ── 3. CONFUSION MATRIX ──────────────────────────────────────
def plot_confusion_matrix(csv_path: Path):
    if not csv_path.exists():
        print("[info] No confusion_matrix.csv found – skipping.")
        return
    cm = pd.read_csv(csv_path, index_col=0)
    labels = [CLASS_INFO[i][0] for i in range(5)]
    fig, ax = plt.subplots(figsize=(8, 6))
    if HAS_SNS:
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=labels, yticklabels=labels, ax=ax)
    else:
        img = ax.imshow(cm.values, cmap="Blues")
        plt.colorbar(img, ax=ax)
        ax.set_xticks(range(5)); ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticks(range(5)); ax.set_yticklabels(labels)
        for i in range(5):
            for j in range(5):
                ax.text(j, i, cm.values[i, j], ha="center", va="center", fontsize=9)
    ax.set_title("Confusion Matrix", fontsize=13)
    ax.set_ylabel("True Label")
    ax.set_xlabel("Predicted Label")
    plt.tight_layout()
    out = OUT_DIR / "confusion_matrix.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[✓] Saved {out}")


# ── MAIN ─────────────────────────────────────────────────────
def main():
    if HAS_RASTERIO and LULC_RASTER.exists():
        with rasterio.open(LULC_RASTER) as src:
            arr = src.read(1)
            pixel_area_ha = abs(src.res[0] * src.res[1]) / 10_000
        print(f"[✓] Raster loaded  shape={arr.shape}  pixel={pixel_area_ha:.4f} ha")
    else:
        print("[demo] Generating synthetic array for demo …")
        rng = np.random.default_rng(42)
        arr = rng.integers(0, 5, size=(500, 500))
        pixel_area_ha = 0.01   # 10 m × 10 m

    df = compute_area_stats(arr, pixel_area_ha)
    print("\nArea statistics:")
    print(df.to_string(index=False))
    df.to_csv(OUT_DIR / "area_statistics.csv", index=False)

    plot_area_bar(df)
    plot_classified_map(arr)
    plot_confusion_matrix(CONFUSION_CSV)
    print("\n[✓] All figures saved to", OUT_DIR)


if __name__ == "__main__":
    main()
