"""
Python / geemap workflow template for Google Earth Engine.

Purpose:
- Authenticate Earth Engine.
- Load Sentinel-2.
- Calculate indices.
- Visualize with geemap.
- Export raster to Google Drive.

Requirements:
pip install earthengine-api geemap eemont geedim
"""

import ee
import geemap

# =======================
# 1. Initialize
# =======================

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()

# =======================
# 2. Editable parameters
# =======================

roi = ee.Geometry.Polygon([
    [[-78.5, -1.0], [-78.5, -1.5], [-78.0, -1.5], [-78.0, -1.0]]
])

start_date = "2024-01-01"
end_date = "2024-12-31"
cloud_threshold = 40
export_scale = 10

# =======================
# 3. Functions
# =======================

def mask_s2_clouds(image):
    """Mask clouds using Sentinel-2 Scene Classification Layer."""
    scl = image.select("SCL")
    mask = (
        scl.neq(3)
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
        .And(scl.neq(11))
    )

    return (
        image.updateMask(mask)
        .divide(10000)
        .copyProperties(image, ["system:time_start"])
    )


def add_indices(image):
    """Add NDVI, EVI, NDWI, MNDWI and NBR."""
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
    mndwi = image.normalizedDifference(["B3", "B11"]).rename("MNDWI")
    nbr = image.normalizedDifference(["B8", "B12"]).rename("NBR")

    evi = image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {
            "NIR": image.select("B8"),
            "RED": image.select("B4"),
            "BLUE": image.select("B2"),
        },
    ).rename("EVI")

    return image.addBands([ndvi, ndwi, mndwi, nbr, evi])


# =======================
# 4. Processing
# =======================

s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi)
    .filterDate(start_date, end_date)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
    .map(mask_s2_clouds)
    .map(add_indices)
)

composite = s2.median().clip(roi)

# =======================
# 5. Visualization
# =======================

Map = geemap.Map()
Map.centerObject(roi, 10)

Map.addLayer(
    composite,
    {"bands": ["B4", "B3", "B2"], "min": 0, "max": 0.3},
    "Sentinel-2 RGB",
)

Map.addLayer(
    composite.select("NDVI"),
    {"min": 0, "max": 1},
    "NDVI",
)

Map.addLayer(roi, {}, "ROI")

# In notebooks, display Map as last object.
Map

# =======================
# 6. Export to Google Drive
# =======================

task = ee.batch.Export.image.toDrive(
    image=composite.select(
        ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "EVI", "NDWI", "MNDWI", "NBR"]
    ),
    description="s2_indices_composite",
    folder="GEE_exports",
    fileNamePrefix="s2_indices_composite",
    region=roi,
    scale=export_scale,
    maxPixels=1e13,
)

task.start()
print("Export task started:", task.status())
