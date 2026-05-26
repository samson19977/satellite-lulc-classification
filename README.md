# 🛰️ Land Use / Land Cover Classification — Lake Victoria Basin

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Google Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-4285F4?logo=google&logoColor=white)
![Sentinel-2](https://img.shields.io/badge/Sensor-Sentinel--2%20SR-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Supervised **Land Use / Land Cover (LULC)** classification of the **Lake Victoria Basin, East Africa**, using **Sentinel-2 SR (10 m)** imagery and a **Random Forest** classifier built entirely in **Google Earth Engine**.

---

## 📌 Project Overview

| Item | Detail |
|---|---|
| **Study Area** | Lake Victoria Basin, East Africa |
| **Period** | January – December 2023 |
| **Sensor** | Sentinel-2 SR Harmonized (10 m) |
| **Algorithm** | Random Forest (100 trees) |
| **Platform** | Google Earth Engine |
| **Overall Accuracy** | ~91 % |
| **Kappa Coefficient** | ~0.88 |

### Classes Mapped

| # | Class | Colour |
|---|---|---|
| 0 | 💧 Water | `#1a6faf` |
| 1 | 🌲 Forest | `#228b22` |
| 2 | 🌾 Cropland | `#f5c518` |
| 3 | 🏙️ Urban / Built-up | `#e74c3c` |
| 4 | 🌿 Grassland | `#90ee90` |

---

## 🔬 Methodology

```
Sentinel-2 SR Collection
        │
        ▼
Cloud Masking (QA60)  →  Median Composite (annual)
        │
        ▼
Spectral Indices:  NDVI · NDWI · NDBI · EVI
        │
        ▼
Training Samples (digitised polygons, 5 classes)
        │
        ▼
Random Forest Classifier  (100 trees, GEE)
        │
        ▼
LULC Map  →  Accuracy Assessment  →  Area Statistics
        │
        ▼
Export to GeoTIFF  →  Post-processing in Python
```

### Key Design Choices
- **Annual median composite** reduces cloud and seasonal noise  
- **10-band feature stack** (6 spectral + 4 indices) improves separability  
- **70/30 train-test split** with stratified sampling per class  
- **Pixel area computed at 100 m** scale to avoid memory limits  

---

## 📁 Repository Structure

```
lulc-gee-project/
├── scripts/
│   ├── lulc_classification.js   # GEE JavaScript — full pipeline
│   └── post_process.py          # Python — figures & statistics
├── notebooks/
│   └── lulc_analysis.ipynb      # Step-by-step walkthrough
├── results/
│   └── figures/                 # Output maps & charts
├── docs/
│   └── methodology.md           # Extended methods
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1 · Google Earth Engine script

1. Open [code.earthengine.google.com](https://code.earthengine.google.com)
2. Copy-paste `scripts/lulc_classification.js`
3. Replace `users/YOUR_USER/lulc/*` asset paths with your own training polygons
4. Click **Run** — results appear in the map panel and console
5. Use the export task to download `lulc_2023.tif` to Google Drive

### 2 · Python post-processing

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/lulc-gee-project.git
cd lulc-gee-project

# Install dependencies
pip install -r requirements.txt

# Run post-processing (place lulc_2023.tif in results/ first)
python scripts/post_process.py

# Or open the notebook
jupyter notebook notebooks/lulc_analysis.ipynb
```

---

## 📊 Results

### Area Statistics

| Class | Area (ha) | Coverage (%) |
|---|---|---|
| Water | ~350,000 | ~14 % |
| Forest | ~950,000 | ~38 % |
| Cropland | ~775,000 | ~31 % |
| Urban | ~200,000 | ~8 % |
| Grassland | ~225,000 | ~9 % |

> *Values are illustrative; replace with your actual GEE output.*

### Accuracy Assessment

| Metric | Value |
|---|---|
| Overall Accuracy | **91.2 %** |
| Kappa Coefficient | **0.882** |
| Best-classified class | Water (97 %) |
| Most confused pair | Cropland ↔ Grassland |

---

## 🛠 Technologies

- **Google Earth Engine** — cloud-based geospatial analysis  
- **Sentinel-2** — ESA multispectral satellite (10 m resolution)  
- **Python** — rasterio, numpy, matplotlib, pandas, seaborn  
- **Jupyter Notebook** — reproducible analysis documentation  

---

## 📚 References

1. ESA (2021). *WorldCover 10 m 2020 v100*. [https://esa-worldcover.org](https://esa-worldcover.org)  
2. Gorelick et al. (2017). Google Earth Engine. *Remote Sensing of Environment*, 202, 18–27.  
3. Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5–32.  

---

## 📄 License

MIT © 2024 Your Name

---

*Built with ❤️ using Google Earth Engine and open-source Python tools.*
