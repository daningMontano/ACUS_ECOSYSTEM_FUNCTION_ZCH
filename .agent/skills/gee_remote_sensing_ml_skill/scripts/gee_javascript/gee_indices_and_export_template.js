// Google Earth Engine JavaScript template
// Purpose: Load Sentinel-2, mask clouds, calculate indices, composite and export.

// =======================
// 1. Editable parameters
// =======================

var roi = /* color: #d63000 */ ee.Geometry.Polygon(
  [[[-78.5, -1.0], [-78.5, -1.5], [-78.0, -1.5], [-78.0, -1.0]]]
);

var startDate = '2024-01-01';
var endDate = '2024-12-31';
var cloudThreshold = 40;
var exportScale = 10;

// =======================
// 2. Cloud mask function
// =======================

function maskS2Clouds(image) {
  var scl = image.select('SCL');

  // Exclude cloud shadow, clouds, cirrus and snow.
  var mask = scl.neq(3)
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));

  return image.updateMask(mask)
    .divide(10000)
    .copyProperties(image, ['system:time_start']);
}

// =======================
// 3. Spectral indices
// =======================

function addIndices(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
  var ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI');
  var mndwi = image.normalizedDifference(['B3', 'B11']).rename('MNDWI');

  var evi = image.expression(
    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
    {
      'NIR': image.select('B8'),
      'RED': image.select('B4'),
      'BLUE': image.select('B2')
    }
  ).rename('EVI');

  var nbr = image.normalizedDifference(['B8', 'B12']).rename('NBR');

  return image.addBands([ndvi, ndwi, mndwi, evi, nbr]);
}

// =======================
// 4. Collection processing
// =======================

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudThreshold))
  .map(maskS2Clouds)
  .map(addIndices);

var composite = s2.median().clip(roi);

// =======================
// 5. Visualization
// =======================

Map.centerObject(roi, 10);

Map.addLayer(
  composite,
  {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3},
  'Sentinel-2 RGB'
);

Map.addLayer(
  composite.select('NDVI'),
  {min: 0, max: 1, palette: ['brown', 'yellow', 'green']},
  'NDVI'
);

// =======================
// 6. Export
// =======================

Export.image.toDrive({
  image: composite.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'EVI', 'NDWI', 'MNDWI', 'NBR']),
  description: 's2_indices_composite',
  folder: 'GEE_exports',
  fileNamePrefix: 's2_indices_composite',
  region: roi,
  scale: exportScale,
  maxPixels: 1e13
});
