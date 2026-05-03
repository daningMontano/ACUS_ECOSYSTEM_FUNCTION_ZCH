# Google Earth Engine Implementation: GEDI + Sentinel + ML

## Tabla de Contenidos
- [Setup GEE + Autenticación](#setup-gee--autenticación)
- [Loading GEDI Collections](#loading-gedi-collections)
- [Sentinel-2 Processing](#sentinel-2-processing)
- [Sentinel-1 SAR Processing](#sentinel-1-sar-processing)
- [Sampling en GEDI Footprints](#sampling-en-gedi-footprints)
- [Feature Stacking y Export](#feature-stacking-y-export)
- [Advanced: Interpolación y Pared a Pared](#advanced-interpolación-y-pared-a-pared)

---

## Setup GEE + Autenticación

### JavaScript Console (GEE Web Editor)

```javascript
// Verificar acceso autenticado
print(ee.currentUser());

// Definir región de interés (AoI)
var aoi = ee.Geometry.Polygon(
  [[
    [-75.5, -5.0],   // noroeste (Amazonas, Brasil)
    [-55.0, -5.0],   // noreste
    [-55.0, -15.0],  // sureste (Mato Grosso)
    [-75.5, -15.0],  // suroeste
    [-75.5, -5.0]    // cierre
  ]],
  null, false  // crs, inverted, planar
);

// Visualizar
Map.addLayer(aoi, {color: 'red'}, 'AoI');
Map.setCenter(-65, -10, 5);  // lon, lat, zoom
```

### Python (ee.Authenticate + Colab)

```python
import ee
import geemap

# Autenticar (primera vez)
ee.Authenticate()

# Inicializar
ee.Initialize(project='your-google-cloud-project')

# O directo en Colab (sin credenciales explícitas)
import geopandas as gpd
aoi = gpd.read_file('aoi.shp')
aoi_ee = ee.Geometry.Polygon(aoi.bounds.values[0].tolist())
```

---

## Loading GEDI Collections

### GEDI L4A (Biomasa) - Colección Principal

```javascript
// Colección GEDI L4A v2.1 (recomendada 2023+)
var gedi_l4a = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_V2_1')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31');

// Inspeccionar estructura
print('GEDI L4A bands:', gedi_l4a.first().bandNames());
// Output: [agbd, agbd_std, l4_quality_flag, degrade_flag, sensor, ...]

// Visualizar footprints (primer imagen)
var gedi_first = gedi_l4a.first();
Map.addLayer(gedi_first.select('agbd'), {min: 0, max: 300, palette: ['blue', 'green', 'yellow', 'red']}, 
  'GEDI L4A AGBD');

// Contar footprints
print('Total GEDI footprints:', gedi_l4a.size());
```

### GEDI L2A (Relative Heights) - Alternativa

```javascript
// Si necesitas métricas de estructura (RH cuantiles)
var gedi_l2a = ee.ImageCollection('LARSE/GEDI/GEDI02_A_002_V2_1')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31');

// L2A tiene: rh0, rh5, ..., rh95, rh100 (101 bandas RH)
// Seleccionar RH de interés
var rh_metrics = gedi_l2a.select(['rh0', 'rh25', 'rh50', 'rh75', 'rh98', 'rh100']);
```

### ICESat-2 ATL08 (Canopy Height) - Para Validación

```javascript
// Colección ICESat-2 (cobertura completa)
var icesat2_atl08 = ee.ImageCollection('ICESAT2/ATL08_V003')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31');

// Filtrar calidad
var icesat2_filtered = icesat2_atl08
  .map(function(img) {
    return img
      .updateMask(img.select('quality_flag').gte(2))
      .updateMask(img.select('signal_confidence').gte(2));
  });

var h_can = icesat2_filtered.select('h_can');
```

---

## Sentinel-2 Processing

### Cloud Masking y Preprocesamiento

```javascript
// Función de cloud masking (calidad pixeles Sentinel-2)
function maskS2clouds(image) {
  var qa = image.select('QA60');
  
  // Bits 10 y 11 son nubes y cirros
  var cloudBitMask = 1 << 10;
  var cirusBitMask = 1 << 11;
  
  // Crear mask
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
    .and(qa.bitwiseAnd(cirusBitMask).eq(0));
  
  // Aplicar y retornar
  return image
    .updateMask(mask)
    .divide(10000)  // Escalar TOA a reflectancia (0-1)
    .select('B.*')  // Solo bandas espectrales
    .copyProperties(image, ['system:time_start']);
}

// Load Sentinel-2 collection
var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .median();  // Imagen compuesta (mediana, reduce ruido)

// Visualizar RGB natural
Map.addLayer(s2.select(['B4', 'B3', 'B2']), {min: 0, max: 0.3}, 'S2 RGB');
```

### Cálculo de Índices Espectrales

```javascript
// Definir bandas (Sentinel-2)
var B2 = s2.select('B2');    // Blue
var B3 = s2.select('B3');    // Green
var B4 = s2.select('B4');    // Red
var B5 = s2.select('B5');    // Red Edge 705
var B6 = s2.select('B6');    // Red Edge 740
var B7 = s2.select('B7');    // Red Edge 783
var B8 = s2.select('B8');    // NIR
var B8A = s2.select('B8A');  // Red Edge 865
var B11 = s2.select('B11');  // SWIR 1610
var B12 = s2.select('B12');  // SWIR 2190

// NDVI (Normalized Difference Vegetation Index)
var ndvi = B8.subtract(B4).divide(B8.add(B4)).rename('NDVI');

// EVI (Enhanced Vegetation Index)
var evi = B8.subtract(B4)
  .multiply(2.5)
  .divide(B8.multiply(6).subtract(B4.multiply(7.5)).add(B2.multiply(1)).add(10000))
  .rename('EVI');

// NDII (Normalized Difference Infrared Index) - Humedad
var ndii = B8.subtract(B11).divide(B8.add(B11)).rename('NDII');

// NDBI (Normalized Difference Built-up Index) - Suelo desnudo
var ndbi = B11.subtract(B8).divide(B11.add(B8)).rename('NDBI');

// Red Edge NDVI (sensible a canopy)
var ndre = B8A.subtract(B5).divide(B8A.add(B5)).rename('NDRE');

// Crear stack de índices
var indices = ndvi.addBands([evi, ndii, ndbi, ndre]);

Map.addLayer(ndvi, {min: 0.3, max: 0.8, palette: ['red', 'yellow', 'green']}, 'NDVI');
```

### Texturas GLCM (Entropy, Contrast)

```javascript
// NOTA: GEE no tiene GLCM nativo. Exportar NDVI → calcular en Python/R localmente
// O usar simplificación: variabilidad local (std dev local)

// Variabilidad local (proxy para heterogeneidad)
var neighborhood = ee.Kernel.circle(150, 'meters');  // 150m radius
var ndvi_std = ndvi.reduceNeighborhood(ee.Reducer.stdDev(), neighborhood)
  .rename('NDVI_Std');  // Textura proxy (heterogeneidad)

var ndvi_mean = ndvi.reduceNeighborhood(ee.Reducer.mean(), neighborhood)
  .rename('NDVI_Mean');

// Ratio
var texture_contrast = ndvi_std.divide(ndvi_mean.add(0.01)).rename('Texture_Contrast');

Map.addLayer(texture_contrast, {min: 0, max: 0.5}, 'Texture Contrast');
```

---

## Sentinel-1 SAR Processing

### VV/VH Backscatter y Filtrado de Speckle

```javascript
// Sentinel-1 (SAR de banda C)
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))  // Modo interferométrico
  .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))  // Ascendentes (evitar effects de topografía)
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', ['VV', 'VH']))
  .map(function(img) {
    // Lee filter (Lee speckle filtering)
    var vv = img.select('VV');
    var vh = img.select('VH');
    
    // Aplicar Lee filter con kernel 5x5
    var vv_filtered = vv.focal_median(2.5, 'meters');
    var vh_filtered = vh.focal_median(2.5, 'meters');
    
    return ee.Image([vv_filtered, vh_filtered])
      .rename(['VV', 'VH'])
      .copyProperties(img, ['system:time_start']);
  })
  .median();  // Compuesta (reduce ruido temporal)

// Extraer variables SAR
var VV = s1.select('VV');
var VH = s1.select('VH');

var vv_vh_ratio = VV.divide(VH.add(0.01)).rename('VV_VH_Ratio');
var vv_vh_sum = VV.add(VH).rename('VV_VH_Sum');
var vv_vh_diff = VV.subtract(VH).rename('VV_VH_Diff');

// Visualizar en dB (log scale)
Map.addLayer(VV.log10().multiply(10), {min: -15, max: 0}, 'Sentinel-1 VV (dB)');
```

### Conversión a dB

```javascript
// SAR backscatter en dB (logarítmico)
var s1_db = s1.log10().multiply(10);

var VV_dB = s1_db.select('VV').rename('VV_dB');
var VH_dB = s1_db.select('VH').rename('VH_dB');

// Ratio en dB es más estable
var vv_vh_ratio_db = VV_dB.subtract(VH_dB).rename('VV_VH_Ratio_dB');
```

---

## Sampling en GEDI Footprints

### Extración de Features en Ubicaciones GEDI

```javascript
// Stack todas features en una sola imagen multi-banda
var features_stack = s2.addBands([
  indices,                    // Sentinel-2 índices
  s1.select(['VV', 'VH']),   // Sentinel-1
  texture_contrast
]);

// Agregar topografía (SRTM)
var dem = ee.Image('USGS/SRTMGL1_Ellip/SRTMGL1_Ellip_srtm');
var slope = ee.Terrain.slope(dem).rename('Slope');
var aspect = ee.Terrain.aspect(dem).rename('Aspect');
var elevation = dem.rename('Elevation');

features_stack = features_stack.addBands([slope, aspect, elevation]);

print('Features stack bands:', features_stack.bandNames());

// **CRÍTICO**: Sample en footprints GEDI
// GEE no puede sample en points arbitrarios eficientemente dentro de ImageCollection
// Necesitamos:
// 1. Convertir GEDI L4A a puntos (footprint centros)
// 2. Sample features_stack en esos puntos

// Extraer geometría de GEDI (centroide footprint)
var gedi_points = gedi_l4a.map(function(img) {
  var agbd = img.select('agbd').reduceRegion(ee.Reducer.mean(), aoi, 30).get('agbd');
  var geometry = img.geometry();
  return ee.Feature(geometry.centroid(), {'agbd': agbd});
}).randomColumn();  // Agregar columa aleatoria para stratified sampling

// Sample features en GEDI points
var training_data = features_stack.sampleRectangles(
  collection=gedi_points,
  defaultValue=0,
  scale=30,
  projection='EPSG:4326'
);

print('Training data properties:', training_data.first().propertyNames());
```

### Alternativa Simplificada: Usar Regiones GEDI

```javascript
// Si prefieres no sample pixel-by-pixel, agregar GEDI como banda directamente
// (requiere que GEDI sea Image Collection con misma resolución)

// Pero GEDI L4A es sparse (25m footprints discontinuos)
// Mejor approach: 
// 1. Resampling GEDI a 30m grid via mean() en footprints
// 2. Sampling + exportación para ML en Python

var gedi_resampled = gedi_l4a.mosaic()  // Fusiona footprints
  .reduceResolution(ee.Reducer.mean(), false, 30)  // Resample a 30m
  .reproject('EPSG:4326', null, 30);

var features_with_gedi = features_stack.addBands(gedi_resampled);
```

---

## Feature Stacking y Export

### Export Completo de Features + Target

```javascript
// Crear tabla de training: features + target (AGBD)
var training_table = features_stack.sampleRectangles(
  collection=gedi_points,
  properties=['agbd'],  // Incluir target
  scale=30,
  projection='EPSG:4326'
);

// Export a CSV en Google Drive
Export.table.toDrive({
  collection: training_table,
  description: 'GEDI_Sentinel_Features_Training',
  folder: 'GEE_Exports',
  fileFormat: 'CSV'
});

// Export a Google Cloud Storage (más rápido para datos grandes)
Export.table.toCloudStorage({
  collection: training_table,
  description: 'GEDI_Training_Data',
  bucket: 'your-gcs-bucket',
  fileNamePrefix: 'gedi_features/training',
  fileFormat: 'CSV'
});

// Monitorear tasks en GEE console
print('Submitting export tasks...');
```

### Export de Grilla de Features (para Mapeo)

```javascript
// Crear grilla regular para predicción espacial
var grid = ee.FeatureCollection.randomPoints(aoi, 100, 0)
  .map(function(pt) {
    return ee.Feature(pt.geometry().buffer(500))  // Buffer 500m alrededor
  });

// Sample features en grilla
var grid_features = features_stack.sampleRectangles(
  collection=grid,
  scale=30
);

// Export
Export.table.toDrive({
  collection: grid_features,
  description: 'GEDI_Grid_Features_Predict',
  fileFormat: 'CSV'
});
```

### Export de Images (GeoTIFF para análisis local)

```javascript
// Exportar índices + SAR como GeoTIFF
Export.image.toDrive({
  image: indices.float(),
  description: 'Sentinel2_Indices',
  folder: 'GEE_Exports',
  scale: 30,
  crs: 'EPSG:4326',
  region: aoi,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});

// Exportar SAR
Export.image.toDrive({
  image: s1.select(['VV', 'VH']).float(),
  description: 'Sentinel1_VV_VH',
  scale: 30,
  region: aoi,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});

// Exportar topografía
Export.image.toDrive({
  image: ee.Image([slope, elevation]).float(),
  description: 'SRTM_Topography',
  scale: 30,
  region: aoi,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});
```

---

## Advanced: Interpolación y Pared a Pared

### Problema: Gaps Orbitales GEDI

GEDI orbita con pass spacing ~25 km entre pases. Resultado: **gaps continuos en mapas**.

```javascript
// Visualizar cobertura de GEDI
var gedi_coverage = gedi_l4a.select('agbd')
  .unmask(0)
  .gte(0)  // Boolean: 1 si GEDI, 0 si gap
  .rename('GEDI_Coverage');

Map.addLayer(gedi_coverage, {min: 0, max: 1, palette: ['white', 'blue']}, 'GEDI Coverage');
```

### Interpolación: Usar Sentinel para Llenar Gaps

```javascript
// Estrategia: Train modelo en GEDI points, predict en grilla continua
// Exportar training data → Colab/RStudio (entrenar RF/XGBoost)
// Importar modelo → GEE para predicción (si GEE RF disponible)

// **Alternativa GEE nativa**: Usar Sentinel indices como proxy directo
// (menos exacto pero rápido)

// Relación simple: NDVI ↔ Biomasa (linear o polynomial)
var ndvi_agbd_regression = gedi_l4a
  .select('agbd')
  .updateMask(ndvi)
  .correlate(ndvi);

// Más sofisticado: RF classifier en GEE
var training = features_stack
  .sampleRectangles(gedi_points, ['agbd'], 30)
  .randomColumn('random', 0)
  .filter(ee.Filter.lt('random', 0.8));  // 80% training

var classifier = ee.Classifier.smileRandomForest(50)  // 50 trees
  .train(training, 'agbd', features_stack.bandNames());

var agbd_predicted = features_stack.classify(classifier, 'agbd_pred');

Map.addLayer(agbd_predicted, {min: 0, max: 300, palette: ['blue', 'green', 'yellow', 'red']}, 
  'Predicted AGBD');
```

### Exportar Mapa Predicho

```javascript
Export.image.toDrive({
  image: agbd_predicted.uint8(),  // 8-bit para menor size
  description: 'GEDI_AGBD_Map_Continuous',
  scale: 30,
  region: aoi,
  maxPixels: 1e13,
  crs: 'EPSG:4326',
  fileFormat: 'GeoTIFF'
});
```

---

## Python Integration: earthengine-api

### Desde Colab

```python
import ee
import geemap
import folium
import pandas as pd

# Autenticar (primera vez)
ee.Authenticate()
ee.Initialize()

# Definir AoI
aoi = ee.Geometry.Polygon([
    [[-75.5, -5.0],
     [-55.0, -5.0],
     [-55.0, -15.0],
     [-75.5, -15.0]]
])

# Load GEDI + Sentinel
gedi = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_V2_1') \
    .filterBounds(aoi) \
    .filterDate('2020-01-01', '2023-12-31')

s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(aoi) \
    .filterDate('2020-01-01', '2023-12-31') \
    .median()

# Calcular NDVI
ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')

# Export
task = ee.batch.Export.image.toDrive(
    image=ndvi,
    description='NDVI_Amazonia',
    folder='GEE_Exports',
    scale=30,
    region=aoi,
    maxPixels=1e13,
    fileFormat='GeoTIFF'
)
task.start()

# Monitorear
import time
while task.active():
    print(f'Task status: {task.status()}')
    time.sleep(5)
print('Export complete!')
```

---

## Troubleshooting Común

### Error: "ImageCollection computation timed out"
**Causa**: Demasiados datos, geometría compleja.
**Solución**: 
```javascript
// Dividir en chunks más pequeños
var chunks = gedi_l4a.filterDate('2020-06-01', '2020-09-01');  // Solo 3 meses
// Procesar separadamente, fusionar después
```

### Error: "Pixel values out of bounds"
**Causa**: Reflectancia > 1 (Sentinel-2 sin normalizar a TOA).
**Solución**:
```javascript
var s2_toa = ee.ImageCollection('COPERNICUS/S2')  // TOA (no SR)
  .map(function(img) {
    return img.divide(10000);  // Escalar manualmente
  });
```

### Performance lento (features en cada footprint)
**Causa**: Sample en toda ImageCollection es O(n).
**Solución**:
```javascript
// Usar mosaic() primero
var gedi_mosaic = gedi_l4a.mosaic();
var features_sampled = features_stack.sampleRectangles(gedi_mosaic, scale=30);
```

