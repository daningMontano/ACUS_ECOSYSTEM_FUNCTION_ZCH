# R / rgee workflow template
# Purpose: Load Sentinel-2, mask clouds, calculate indices, visualize and export.

# install.packages("rgee")
# install.packages("sf")

library(rgee)
library(sf)

# =======================
# 1. Initialize
# =======================

ee_Initialize()

# =======================
# 2. Editable parameters
# =======================

roi <- ee$Geometry$Polygon(list(list(
  c(-78.5, -1.0),
  c(-78.5, -1.5),
  c(-78.0, -1.5),
  c(-78.0, -1.0),
  c(-78.5, -1.0)
)))

start_date <- "2024-01-01"
end_date <- "2024-12-31"
cloud_threshold <- 40
export_scale <- 10

# =======================
# 3. Functions
# =======================

mask_s2_clouds <- function(image) {
  scl <- image$select("SCL")

  mask <- scl$neq(3)$
    And(scl$neq(8))$
    And(scl$neq(9))$
    And(scl$neq(10))$
    And(scl$neq(11))

  image$
    updateMask(mask)$
    divide(10000)$
    copyProperties(image, list("system:time_start"))
}

add_indices <- function(image) {
  ndvi <- image$normalizedDifference(list("B8", "B4"))$rename("NDVI")
  ndwi <- image$normalizedDifference(list("B3", "B8"))$rename("NDWI")
  mndwi <- image$normalizedDifference(list("B3", "B11"))$rename("MNDWI")
  nbr <- image$normalizedDifference(list("B8", "B12"))$rename("NBR")

  evi <- image$expression(
    "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
    list(
      NIR = image$select("B8"),
      RED = image$select("B4"),
      BLUE = image$select("B2")
    )
  )$rename("EVI")

  image$addBands(list(ndvi, ndwi, mndwi, nbr, evi))
}

# =======================
# 4. Processing
# =======================

s2 <- ee$ImageCollection("COPERNICUS/S2_SR_HARMONIZED")$
  filterBounds(roi)$
  filterDate(start_date, end_date)$
  filter(ee$Filter$lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))$
  map(mask_s2_clouds)$
  map(add_indices)

composite <- s2$median()$clip(roi)

# =======================
# 5. Visualization
# =======================

Map$centerObject(roi, 10)

Map$addLayer(
  composite,
  list(bands = c("B4", "B3", "B2"), min = 0, max = 0.3),
  "Sentinel-2 RGB"
)

Map$addLayer(
  composite$select("NDVI"),
  list(min = 0, max = 1),
  "NDVI"
)

# =======================
# 6. Export
# =======================

task <- ee$batch$Export$image$toDrive(
  image = composite$select(c(
    "B2", "B3", "B4", "B8", "B11", "B12",
    "NDVI", "EVI", "NDWI", "MNDWI", "NBR"
  )),
  description = "s2_indices_composite",
  folder = "GEE_exports",
  fileNamePrefix = "s2_indices_composite",
  region = roi,
  scale = export_scale,
  maxPixels = 1e13
)

task$start()
task$status()
