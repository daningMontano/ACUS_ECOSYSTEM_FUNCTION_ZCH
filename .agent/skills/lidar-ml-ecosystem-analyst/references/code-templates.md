# Code Templates: Python, R, JavaScript

Snippets listos para copiar-pegar, adaptables a proyectos específicos.

## Tabla de Contenidos
- [Python/Colab: Pipeline Completo](#pythoncolab-pipeline-completo)
- [R: rGEDI + Descarga + ML](#r-rgedi--descarga--ml)
- [JavaScript/GEE: Script Completo](#javascriptgee-script-completo)

---

## Python/Colab: Pipeline Completo

### Setup Inicial

```python
# INSTALACIÓN (ejecutar una sola vez en Colab)
!pip install earthengine-api geopandas rasterio xgboost lightgbm optuna shap folium
!pip install scikit-learn scikit-image pandas numpy matplotlib seaborn scipy

# IMPORTS
import ee
import pandas as pd
import numpy as np
import geopandas as gpd
import rasterio
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# CONFIGURACIÓN COLAB
from google.colab import auth
auth.authenticate_user()

# AUTENTICAR EE
ee.Authenticate()
ee.Initialize(project='your-gcp-project-id')

print("✓ Setup completo")
```

### Descarga de GEDI L4A

```python
# DEFINIR REGIÓN (ajustar bbox y fechas)
bbox = [-75.5, -5.0, -55.0, -15.0]  # [lon_min, lat_min, lon_max, lat_max] Amazonas
date_range = ('2021-01-01', '2023-12-31')

aoi = ee.Geometry.Polygon([
    [[bbox[0], bbox[1]],
     [bbox[2], bbox[1]],
     [bbox[2], bbox[3]],
     [bbox[0], bbox[3]],
     [bbox[0], bbox[1]]]
])

# CARGAR GEDI L4A
gedi_col = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_V2_1') \
    .filterBounds(aoi) \
    .filterDate(date_range[0], date_range[1])

print(f"Total GEDI footprints: {gedi_col.size().getInfo()}")

# APLICAR FILTROS MULTICAPA
def filter_gedi_quality(image):
    """Filtrado de calidad GEDI"""
    return image \
        .updateMask(image.select('l4_quality_flag').eq(1)) \
        .updateMask(image.select('degrade_flag').eq(0)) \
        .updateMask(image.select('sds_quality').eq(1)) \
        .copyProperties(image)

gedi_clean = gedi_col.map(filter_gedi_quality)

print(f"GEDI tras filtrado de calidad: {gedi_clean.size().getInfo()}")

# CREAR PUNTOS DE FOOTPRINTS (centroides)
def extract_gedi_points(image):
    """Extraer puntos GEDI con propiedades"""
    geom = image.geometry()
    props = image.select(['agbd', 'agbd_std', 'sensitivity']).sampleRectangles(
        collection=ee.FeatureCollection([ee.Feature(geom)]),
        defaultValue=0,
        scale=30
    ).first().toDictionary()
    
    return ee.Feature(geom.centroid(), props)

gedi_points = gedi_clean.map(extract_gedi_points)

# EXPORTAR A CSV
task = ee.batch.Export.table.toDrive(
    collection=gedi_points,
    description='GEDI_L4A_Points_Training',
    folder='GEE_Exports',
    fileFormat='CSV',
    selectors=['agbd', 'agbd_std', 'sensitivity', 'geometry']
)
task.start()

print(f"Export iniciado. Monitorear en GEE Tasks.")
```

### Procesar Sentinel-2 + Índices

```python
# CARGAR Y LIMPIAR SENTINEL-2
def mask_s2_clouds(image):
    """Cloud masking Sentinel-2"""
    qa = image.select('QA60')
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0)
    cirrus_mask = qa.bitwiseAnd(1 << 11).eq(0)
    return image.updateMask(cloud_mask.And(cirrus_mask)).divide(10000)

s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(aoi) \
    .filterDate(date_range[0], date_range[1]) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
    .map(mask_s2_clouds) \
    .median()  # Composición (reduce ruido)

# CALCULAR ÍNDICES ESPECTRALES
B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 = \
    s2.select('B2'), s2.select('B3'), s2.select('B4'), s2.select('B5'), \
    s2.select('B6'), s2.select('B7'), s2.select('B8'), s2.select('B8A'), \
    s2.select('B11'), s2.select('B12')

ndvi = B8.subtract(B4).divide(B8.add(B4)).rename('NDVI')
evi = B8.subtract(B4).multiply(2.5) \
    .divide(B8.multiply(6).subtract(B4.multiply(7.5)).add(B2.multiply(1))) \
    .rename('EVI')
ndii = B8.subtract(B11).divide(B8.add(B11)).rename('NDII')
ndbi = B11.subtract(B8).divide(B11.add(B8)).rename('NDBI')
ndre = B8A.subtract(B5).divide(B8A.add(B5)).rename('NDRE')

indices = ndvi.addBands([evi, ndii, ndbi, ndre])

# TOPOGRAFÍA
dem = ee.Image('USGS/SRTMGL1_Ellip/SRTMGL1_Ellip_srtm')
slope = ee.Terrain.slope(dem).rename('Slope')
elevation = dem.rename('Elevation')

# STACK TODO
features_stack = s2.select(['B2', 'B4', 'B8']).addBands([
    indices, slope, elevation
])

print(f"Features stack bands: {features_stack.bandNames().getInfo()}")
```

### Sample Features en GEDI + Export

```python
# SAMPLE FEATURES EN PUNTOS GEDI
training_data = features_stack.samplePoints(
    collection=gedi_points,
    scale=30,
    geometries=True
)

# EXPORT
task_features = ee.batch.Export.table.toDrive(
    collection=training_data,
    description='GEDI_Sentinel_Features_Training',
    folder='GEE_Exports',
    fileFormat='CSV'
)
task_features.start()

print("Features export iniciado...")
```

### Descarguar y Cargar en Colab

```python
# Una vez exportados los archivos en Google Drive:
# 1. Abrir Google Drive en nueva pestaña
# 2. Navegar a GEE_Exports
# 3. Descargar CSV

# O automático desde Colab:
from google.colab import files
import os

# Montar Drive
from google.colab import drive
drive.mount('/content/drive')

# Copiar archivos
!cp "/content/drive/My Drive/GEE_Exports/GEDI_Sentinel_Features_Training.csv" .

# Cargar en pandas
df = pd.read_csv('GEDI_Sentinel_Features_Training.csv')
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(df.head())

# Limpieza básica
df = df.dropna()  # Remover NaN
print(f"Dataset limpio: {df.shape}")
```

### Training ML (Random Forest + XGBoost)

```python
# PREPARAR FEATURES Y TARGET
feature_cols = [col for col in df.columns if col not in 
                ['agbd', 'agbd_std', 'geometry', 'system:index']]

X = df[feature_cols].values
y = df['agbd'].values
coords = df[['lon', 'lat']].values

# NORMALIZAR FEATURES
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PARTICIONAMIENTO GEOGRÁFICO (NO random!)
from sklearn.cluster import KMeans

n_folds = 5
kmeans = KMeans(n_clusters=n_folds, random_state=42)
clusters = kmeans.fit_predict(coords)

# Train: 70%, Val: 15%, Test: 15%
train_idx = np.where(clusters.isin([0, 1, 2]))[0]
val_idx = np.where(clusters == 3)[0]
test_idx = np.where(clusters == 4)[0]

X_train, X_val, X_test = X_scaled[train_idx], X_scaled[val_idx], X_scaled[test_idx]
y_train, y_val, y_test = y[train_idx], y[val_idx], y[test_idx]

print(f"Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(test_idx)}")

# --- RANDOM FOREST ---
print("\n=== RANDOM FOREST ===")
rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=4,
    n_jobs=-1,
    random_state=42
)
rf.fit(X_train, y_train)

y_val_pred_rf = rf.predict(X_val)
y_test_pred_rf = rf.predict(X_test)

rmse_val_rf = np.sqrt(mean_squared_error(y_val, y_val_pred_rf))
rmse_test_rf = np.sqrt(mean_squared_error(y_test, y_test_pred_rf))
r2_test_rf = r2_score(y_test, y_test_pred_rf)

print(f"Validation RMSE: {rmse_val_rf:.2f} Mg/ha")
print(f"Test RMSE: {rmse_test_rf:.2f} Mg/ha")
print(f"Test R²: {r2_test_rf:.3f}")

# Feature importance
feature_imp = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)
print("\nTop 10 features RF:")
print(feature_imp.head(10))

# --- XGBOOST ---
print("\n=== XGBOOST ===")
xgb_model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
xgb_model.fit(X_train, y_train, 
              eval_set=[(X_val, y_val)],
              early_stopping_rounds=30,
              verbose=False)

y_test_pred_xgb = xgb_model.predict(X_test)
rmse_test_xgb = np.sqrt(mean_squared_error(y_test, y_test_pred_xgb))
r2_test_xgb = r2_score(y_test, y_test_pred_xgb)

print(f"Test RMSE: {rmse_test_xgb:.2f} Mg/ha")
print(f"Test R²: {r2_test_xgb:.3f}")

# Feature importance XGBoost
feature_imp_xgb = pd.DataFrame({
    'feature': feature_cols,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)
print("\nTop 10 features XGBoost:")
print(feature_imp_xgb.head(10))
```

### Evaluación y Validación

```python
# MÉTRICAS ESTÁNDAR
def evaluate_model(y_true, y_pred, model_name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    rrmse = 100 * rmse / y_true.mean()
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    bias = (y_pred - y_true).mean()
    
    print(f"\n{model_name} - Test Set Metrics:")
    print(f"  RMSE: {rmse:.2f} Mg/ha")
    print(f"  RRMSE: {rrmse:.1f}%")
    print(f"  MAE: {mae:.2f} Mg/ha")
    print(f"  R²: {r2:.3f}")
    print(f"  Bias: {bias:.2f} Mg/ha")
    
    return {'RMSE': rmse, 'RRMSE': rrmse, 'MAE': mae, 'R2': r2, 'Bias': bias}

metrics_rf = evaluate_model(y_test, y_test_pred_rf, "Random Forest")
metrics_xgb = evaluate_model(y_test, y_test_pred_xgb, "XGBoost")

# VALIDACIÓN POR ESTRATOS DE BIOMASA
print("\n=== VALIDACIÓN POR ESTRATOS ===")
strata = [
    (0, 100, 'Bajo'),
    (100, 200, 'Medio'),
    (200, 350, 'Alto')
]

for min_b, max_b, label in strata:
    mask = (y_test >= min_b) & (y_test < max_b)
    if mask.sum() > 5:
        y_true_s = y_test[mask]
        y_pred_s_rf = y_test_pred_rf[mask]
        y_pred_s_xgb = y_test_pred_xgb[mask]
        
        rmse_rf_s = np.sqrt(mean_squared_error(y_true_s, y_pred_s_rf))
        rmse_xgb_s = np.sqrt(mean_squared_error(y_true_s, y_pred_s_xgb))
        
        print(f"{label} ({min_b}-{max_b} Mg/ha): "
              f"RF RMSE={rmse_rf_s:.1f}, XGB RMSE={rmse_xgb_s:.1f}, N={mask.sum()}")

# PLOTS DE VALIDACIÓN
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Predicted vs Observed (RF)
axes[0, 0].scatter(y_test, y_test_pred_rf, alpha=0.5, s=20)
lim = [y_test.min(), y_test.max()]
axes[0, 0].plot(lim, lim, 'r--', lw=2)
axes[0, 0].set_xlabel('Observado (Mg/ha)')
axes[0, 0].set_ylabel('Predicho (Mg/ha)')
axes[0, 0].set_title(f'Random Forest (R²={r2_test_rf:.3f})')

# Predicted vs Observed (XGBoost)
axes[0, 1].scatter(y_test, y_test_pred_xgb, alpha=0.5, s=20, color='orange')
axes[0, 1].plot(lim, lim, 'r--', lw=2)
axes[0, 1].set_xlabel('Observado (Mg/ha)')
axes[0, 1].set_ylabel('Predicho (Mg/ha)')
axes[0, 1].set_title(f'XGBoost (R²={r2_test_xgb:.3f})')

# Residuales RF
residuals_rf = y_test - y_test_pred_rf
axes[1, 0].scatter(y_test_pred_rf, residuals_rf, alpha=0.5, s=20)
axes[1, 0].axhline(y=0, color='r', linestyle='--', lw=2)
axes[1, 0].set_xlabel('Predicho (Mg/ha)')
axes[1, 0].set_ylabel('Residual (Mg/ha)')
axes[1, 0].set_title('Random Forest Residuals')

# Distribución residuales
axes[1, 1].hist(residuals_rf, bins=30, alpha=0.5, label='RF', edgecolor='black')
residuals_xgb = y_test - y_test_pred_xgb
axes[1, 1].hist(residuals_xgb, bins=30, alpha=0.5, label='XGB', edgecolor='black')
axes[1, 1].axvline(x=0, color='r', linestyle='--', lw=2)
axes[1, 1].set_xlabel('Residual (Mg/ha)')
axes[1, 1].set_ylabel('Frecuencia')
axes[1, 1].set_title('Distribución Residuales')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('validation_results.png', dpi=150, bbox_inches='tight')
plt.show()

# Guardar modelos
import pickle
with open('rf_model.pkl', 'wb') as f:
    pickle.dump(rf, f)
with open('xgb_model.pkl', 'wb') as f:
    pickle.dump(xgb_model, f)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("\n✓ Modelos guardados")
```

---

## R: rGEDI + Descarga + ML

### Setup

```r
# INSTALACIÓN
install.packages(c("rGEDI", "terra", "sf", "caret", "randomForest", "xgboost", "lightgbm"))
library(rGEDI)
library(terra)
library(sf)
library(caret)
library(randomForest)
library(xgboost)
library(dplyr)
library(ggplot2)

# SET EARTHDATA CREDENTIALS
set_earthdata_user("your_username", "your_password")

# AOI (Amazonas, Brasil)
aoi <- st_polygon(list(rbind(
  c(-75.5, -5), c(-55, -5), c(-55, -15), 
  c(-75.5, -15), c(-75.5, -5)
)))
aoi <- st_sfc(aoi, crs = 4326)

print("✓ Setup R completo")
```

### Descarga GEDI con rGEDI

```r
# DESCARGA GEDI L4A automática
gedi_data <- gedilevel4a(
  filepath = ".",  # directorio local
  version = "002_05",
  degrade = 0,
  quality = 1,
  beam = c("BEAM0101", "BEAM0110", "BEAM1000", "BEAM1011"),
  bbox = c(-75.5, -15, -55, -5)
)

# SIMPLIFICAR (automatiza algunos filtros)
gedi_simple <- gedisimplify(gedi_data, output = "all")

# A data frame
gedi_df <- as.data.frame(gedi_simple@data)

print(dim(gedi_df))
print(colnames(gedi_df))

# FILTRADO ADICIONAL (manual)
gedi_clean <- gedi_df %>%
  filter(l4_quality_flag == 1,
         degrade_flag == 0,
         sensitivity > 0.98,
         agbd_std / agbd < 0.50,  # Error < 50%
         agbd >= 50 & agbd <= 350)  # Rango Amazonía

print(paste("Footprints originales:", nrow(gedi_df)))
print(paste("Footprints limpios:", nrow(gedi_clean)))
```

### Cargar Sentinel-2 en R

```r
# Usar mapas pre-procesados (exported de GEE como GeoTIFF)
# O: usar el paquete "sen2r" (lento pero posible)

# Opción simplificada: cargar GeoTIFF desde GEE export
ndvi_file <- "NDVI_Amazonias.tif"
ndvi_rast <- rast(ndvi_file)

evi_file <- "EVI_Amazonia.tif"
evi_rast <- rast(evi_file)

slope_file <- "Slope_Amazonia.tif"
slope_rast <- rast(slope_file)

# Stack todo en single raster
features_stack <- c(ndvi_rast, evi_rast, slope_rast)
names(features_stack) <- c('ndvi', 'evi', 'slope')

# Convertir GEDI a sf para extracción
gedi_sf <- st_as_sf(gedi_clean, coords = c("lon", "lat"), crs = 4326)

# SAMPLE features en GEDI points
gedi_sf <- gedi_sf %>%
  mutate(
    ndvi = terra::extract(ndvi_rast, gedi_sf)[,2],
    evi = terra::extract(evi_rast, gedi_sf)[,2],
    slope = terra::extract(slope_rast, gedi_sf)[,2]
  )

# A data frame
gedi_ml <- st_drop_geometry(gedi_sf)

print(head(gedi_ml))
```

### ML en R

```r
# PREPARAR DATA
feature_cols <- c('rh50', 'rh25', 'rh75', 'ndvi', 'evi', 'slope')
X <- gedi_ml[, feature_cols] %>% as.matrix()
y <- gedi_ml$agbd

# NORMALIZAR
preproc <- preProcess(X, method = c("center", "scale"))
X_scaled <- predict(preproc, X)

# PARTICIONAMIENTO GEOGRÁFICO
coords <- gedi_ml[, c('lon', 'lat')] %>% as.matrix()
kmeans_cl <- kmeans(coords, centers = 5, nstart = 10)
clusters <- kmeans_cl$cluster

train_idx <- which(clusters %in% 1:3)
val_idx <- which(clusters == 4)
test_idx <- which(clusters == 5)

X_train <- X_scaled[train_idx, ]
X_val <- X_scaled[val_idx, ]
X_test <- X_scaled[test_idx, ]
y_train <- y[train_idx]
y_val <- y[val_idx]
y_test <- y[test_idx]

# RANDOM FOREST
rf_model <- randomForest(
  X_train, y_train,
  ntree = 200,
  max_depth = 12,
  sampsize = nrow(X_train),
  importance = TRUE
)

y_pred_test <- predict(rf_model, X_test)
rmse_test <- sqrt(mean((y_test - y_pred_test)^2))
r2_test <- 1 - sum((y_test - y_pred_test)^2) / sum((y_test - mean(y_test))^2)

print(paste("RF RMSE:", round(rmse_test, 2)))
print(paste("RF R²:", round(r2_test, 3)))

# Feature importance
importance_rf <- importance(rf_model) %>%
  as.data.frame() %>%
  rownames_to_column("Feature") %>%
  arrange(desc(IncNodePurity)) %>%
  head(10)

print(importance_rf)

# XGBOOST
xgb_matrix_train <- xgb.DMatrix(X_train, label = y_train)
xgb_matrix_test <- xgb.DMatrix(X_test, label = y_test)

xgb_params <- list(
  objective = "reg:squarederror",
  eta = 0.05,
  max_depth = 8,
  subsample = 0.8
)

xgb_model <- xgb.train(
  params = xgb_params,
  data = xgb_matrix_train,
  nrounds = 200,
  watchlist = list(test = xgb_matrix_test),
  early_stopping_rounds = 30,
  verbose = 0
)

y_pred_xgb <- predict(xgb_model, xgb_matrix_test)
rmse_xgb <- sqrt(mean((y_test - y_pred_xgb)^2))
r2_xgb <- 1 - sum((y_test - y_pred_xgb)^2) / sum((y_test - mean(y_test))^2)

print(paste("XGB RMSE:", round(rmse_xgb, 2)))
print(paste("XGB R²:", round(r2_xgb, 3)))

# Guardar modelos
saveRDS(rf_model, "rf_model.rds")
saveRDS(xgb_model, "xgb_model.rds")
```

### Validación en R

```r
# MÉTRICAS
results_df <- data.frame(
  Model = c("RF", "XGB"),
  RMSE = c(rmse_test, rmse_xgb),
  R2 = c(r2_test, r2_xgb),
  RRMSE_pct = c(100 * rmse_test / mean(y_test), 100 * rmse_xgb / mean(y_test))
)
print(results_df)

# PLOTS
par(mfrow = c(2, 2))

# Predicted vs Observed (RF)
plot(y_test, y_pred_test, main = "RF: Predicted vs Observed",
     xlab = "Observado (Mg/ha)", ylab = "Predicho (Mg/ha)", pch = 16, alpha = 0.5)
abline(0, 1, col = "red", lwd = 2)

# Predicted vs Observed (XGB)
plot(y_test, y_pred_xgb, main = "XGB: Predicted vs Observed",
     xlab = "Observado (Mg/ha)", ylab = "Predicho (Mg/ha)", pch = 16, alpha = 0.5, col = "orange")
abline(0, 1, col = "red", lwd = 2)

# Residuales
residuals_rf <- y_test - y_pred_test
plot(y_pred_test, residuals_rf, main = "RF: Residuals",
     xlab = "Predicho (Mg/ha)", ylab = "Residual", pch = 16)
abline(h = 0, col = "red", lwd = 2)

# Histograma residuales
hist(residuals_rf, breaks = 30, main = "RF: Distribución Residuales", 
     xlab = "Residual (Mg/ha)", col = "lightblue", edgecolor = "black")

par(mfrow = c(1, 1))
```

---

## JavaScript/GEE: Script Completo

Copiar en GEE Web Code Editor (https://code.earthengine.google.com/)

```javascript
// ============================================
// GEDI + Sentinel-2 + ML Pipeline en GEE
// ============================================

// REGIÓN DE INTERÉS (Amazonas, Brasil)
var aoi = ee.Geometry.Polygon(
  [[[-75.5, -5.0],
    [-55.0, -5.0],
    [-55.0, -15.0],
    [-75.5, -15.0]]]
);

Map.setCenter(-65, -10, 5);
Map.addLayer(aoi, {color: 'FF0000'}, 'AoI');

// ============================================
// 1. CARGAR Y FILTRAR GEDI L4A
// ============================================

var gedi_col = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_V2_1')
  .filterBounds(aoi)
  .filterDate('2021-01-01', '2023-12-31');

print('Total GEDI footprints:', gedi_col.size());

// Filtrado multicapa
var gedi_filtered = gedi_col.map(function(image) {
  return image
    .updateMask(image.select('l4_quality_flag').eq(1))
    .updateMask(image.select('degrade_flag').eq(0))
    .updateMask(image.select('sds_quality').eq(1));
});

print('GEDI tras filtrado:', gedi_filtered.size());

// Visualizar AGBD
var agbd_vis = {min: 50, max: 300, palette: ['blue', 'green', 'yellow', 'red']};
Map.addLayer(gedi_filtered.select('agbd'), agbd_vis, 'GEDI AGBD');

// ============================================
// 2. PROCESAR SENTINEL-2
// ============================================

function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
    .and(qa.bitwiseAnd(cirusBitMask).eq(0));
  return image.updateMask(mask).divide(10000);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(aoi)
  .filterDate('2021-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .median();

Map.addLayer(s2.select(['B4', 'B3', 'B2']), {min: 0, max: 0.3}, 'S2 RGB');

// ÍNDICES ESPECTRALES
var B4 = s2.select('B4');
var B5 = s2.select('B5');
var B8 = s2.select('B8');
var B8A = s2.select('B8A');
var B11 = s2.select('B11');

var ndvi = B8.subtract(B4).divide(B8.add(B4)).rename('NDVI');
var evi = B8.subtract(B4).multiply(2.5)
  .divide(B8.multiply(6).subtract(B4.multiply(7.5)).add(1)).rename('EVI');
var ndii = B8.subtract(B11).divide(B8.add(B11)).rename('NDII');
var ndre = B8A.subtract(B5).divide(B8A.add(B5)).rename('NDRE');

var indices = ndvi.addBands([evi, ndii, ndre]);

Map.addLayer(ndvi, {min: 0.3, max: 0.8, palette: ['red', 'yellow', 'green']}, 'NDVI');

// TOPOGRAFÍA
var dem = ee.Image('USGS/SRTMGL1_Ellip/SRTMGL1_Ellip_srtm');
var slope = ee.Terrain.slope(dem).rename('Slope');
var elevation = dem.rename('Elevation');

// STACK FEATURES
var features_stack = s2.select(['B2', 'B4', 'B8'])
  .addBands(indices)
  .addBands([slope, elevation]);

// ============================================
// 3. CREAR TRAINING DATA
// ============================================

// Convertir GEDI a puntos
var gedi_points = gedi_filtered.map(function(image) {
  var geom = image.geometry();
  var agbd = image.select('agbd').reduceRegion(ee.Reducer.mean(), geom, 30).get('agbd');
  return ee.Feature(geom.centroid(), {'agbd': agbd, 'sensor': 'GEDI'});
});

print('GEDI points:', gedi_points.size());

// SAMPLE FEATURES EN GEDI POINTS
var training_data = features_stack.sampleRectangles({
  collection: gedi_points,
  defaultValue: 0,
  scale: 30,
  geometries: true
});

// EXPORTAR
Export.table.toDrive({
  collection: training_data,
  description: 'GEDI_Sentinel_Training_Data',
  folder: 'GEE_Exports',
  fileFormat: 'CSV'
});

// ============================================
// 4. PREDICCIÓN CON RANDOM FOREST EN GEE
// ============================================

// Train Random Forest (GEE built-in)
var classifier = ee.Classifier.smileRandomForest(50)
  .train(training_data, 'agbd', features_stack.bandNames());

// Clasificar (predecir AGBD)
var agbd_predicted = features_stack.classify(classifier, 'agbd_pred');

// Visualizar mapa predicho
Map.addLayer(agbd_predicted, agbd_vis, 'Predicted AGBD');

// EXPORTAR MAPA
Export.image.toDrive({
  image: agbd_predicted.uint16(),
  description: 'AGBD_Predicted_Map',
  folder: 'GEE_Exports',
  scale: 30,
  region: aoi,
  maxPixels: 1e13,
  crs: 'EPSG:4326'
});

print('✓ Exports enviados a Google Drive');
```

---

## Tips de Debugging

**Python/Colab**:
- Si `ee.Initialize()` falla: `ee.Authenticate()` de nuevo
- Si Sentinel-2 vacío: revisar `CLOUDY_PIXEL_PERCENTAGE` threshold
- Si features_stack muy lento: usar `.median()` en lugar de `.mosaic()`

**R**:
- Si `set_earthdata_user()` falla: usar `Sys.setenv(EARTHDATA_USER=..., EARTHDATA_PASSWORD=...)`
- Si rGEDI descarga interrumpida: retomar manualmente con ruta local

**GEE**:
- Si task "timeouts": dividir región en chunks más pequeños
- Si ImageCollection vacía: verificar `filterDate()` (fechas correctas)
- Si export lento: reducir `scale` (30m es default, pasar a 100m si tiempo crítico)

