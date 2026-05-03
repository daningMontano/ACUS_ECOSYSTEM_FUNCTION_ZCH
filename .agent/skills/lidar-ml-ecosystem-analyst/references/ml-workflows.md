# Machine Learning Workflows: RF, XGBoost, LightGBM

## Tabla de Contenidos
- [Pipeline Estándar](#pipeline-estándar)
- [Feature Engineering](#feature-engineering)
- [Train/Val/Test Splitting](#trainvaltest-splitting)
- [Tuning de Hiperparámetros](#tuning-de-hiperparámetros)
- [Evaluación y Validación](#evaluación-y-validación)
- [Random Forest: Detalles](#random-forest-detalles)
- [XGBoost: Detalles](#xgboost-detalles)
- [LightGBM: Detalles](#lightgbm-detalles)
- [Comparación RF vs XGBoost vs LightGBM](#comparación-rf-vs-xgboost-vs-lightgbm)

---

## Pipeline Estándar

```
1. CARGA DE DATOS
   ├─ GEDI L4A (footprints con AGBD)
   ├─ Sentinel-2 (índices espectrales)
   ├─ Sentinel-1 (backscatter SAR)
   ├─ SRTM/TanDEM-X (topografía)
   └─ Datos de validación de campo (si disponibles)

2. EXPLORATORIO (EDA)
   ├─ Distribuciones de variables
   ├─ Correlaciones (Pearson, Spearman)
   ├─ Valores faltantes (NA, NaN)
   └─ Outliers (boxplot, IQR)

3. LIMPIEZA Y PRE-PROCESAMIENTO
   ├─ Imputación de faltantes
   ├─ Detección de outliers extremos
   ├─ Normalización/escalado (StandardScaler, RobustScaler)
   └─ Balanceo de clases (si regresión estratificada)

4. FEATURE ENGINEERING
   ├─ GEDI métricas (RH cuantiles, índices)
   ├─ Sentinel-2 índices (NDVI, EVI, NDII, NDBI)
   ├─ Texturas GLCM (contraste, disimilaridad, entropía)
   ├─ Sentinel-1 ratio (VV/VH, VV+VH)
   ├─ Topografía (slope, aspect, curvatura)
   └─ Interacciones (RH50*NDVI, etc.)

5. PARTICIONAMIENTO ESPACIAL (NO aleatorio!)
   ├─ Train: 60-70% datos (región geográfica coherente)
   ├─ Validation: 10-20% (región diferente)
   └─ Test: 10-20% (región completamente nueva)

6. AJUSTE DE HIPERPARÁMETROS
   ├─ Búsqueda (Random/Grid/Bayesian)
   ├─ Métrica: RMSE, MAE, R² (validación set)
   ├─ Validación cruzada geográfica K-fold
   └─ Early stopping (para Boosting)

7. ENTRENAMIENTO DEL MODELO FINAL
   ├─ Entrenar con train+val (combo)
   ├─ Usar hiperparámetros optimizados
   └─ Guardar modelo (.pkl, .joblib)

8. EVALUACIÓN EN TEST SET
   ├─ RMSE, RRMSE (%), MAE, R²
   ├─ Bias (mean residual)
   ├─ Análisis por estratos (biomasa baja/media/alta)
   └─ Plots: predicted vs observed, residuals

9. INTERPRETABILIDAD
   ├─ Feature importance (built-in)
   ├─ SHAP values (local + global)
   ├─ Partial dependence plots
   └─ Análisis de errores grandes

10. MAPEO ESPACIAL
    ├─ Predicción en grilla continua
    ├─ Exportar GeoTIFF
    └─ Mapear incertidumbre (std dev)
```

---

## Feature Engineering

### GEDI Métricas

```python
# RH cuantiles (directamente del archivo)
features = {
    'rh0': data['relative_h'][:, 0],    # Altura mínima detectada
    'rh25': data['relative_h'][:, 25],
    'rh50': data['relative_h'][:, 50],  # Mediana (muy predictiva)
    'rh75': data['relative_h'][:, 75],
    'rh98': data['relative_h'][:, 98],  # Casi máximo (saturación)
    'rh100': data['relative_h'][:, 100],  # Máximo
}

# Índices derivados
features['rh_amplitude'] = features['rh100'] - features['rh0']  # Rango total
features['rh_range_25_75'] = features['rh75'] - features['rh25']  # IQR
features['rh_ratio_50_100'] = features['rh50'] / (features['rh100'] + 1e-6)  # Forma
features['rh_uniformity'] = features['rh25'] / (features['rh75'] + 1e-6)  # 1.0=uniforme

# Detectar saturación
features['rh_amp_low'] = (features['rh_amplitude'] < 15).astype(int)  # Flag saturación
```

### Sentinel-2 Índices Espectrales

```python
# Bandas USGS nombrado
B2 = S2['B2']  # Blue
B3 = S2['B3']  # Green
B4 = S2['B4']  # Red
B5 = S2['B5']  # Red Edge 705nm
B6 = S2['B6']  # Red Edge 740nm
B7 = S2['B7']  # Red Edge 783nm
B8 = S2['B8']  # NIR
B8A = S2['B8A']  # Red Edge 865nm
B11 = S2['B11']  # SWIR
B12 = S2['B12']  # SWIR

# Índices estándar
features['ndvi'] = (B8 - B4) / (B8 + B4 + 1e-6)
features['evi'] = 2.5 * (B8 - B4) / (B8 + 6*B4 - 7.5*B2 + 1e-6)
features['ndii'] = (B8 - B11) / (B8 + B11 + 1e-6)  # Humedad vegetación
features['ndbi'] = (B11 - B8) / (B11 + B8 + 1e-6)  # Built-up, bare soil
features['ndre'] = (B8A - B5) / (B8A + B5 + 1e-6)  # Red Edge (canopy)

# Ratios Red Edge (sensibles a estructura)
features['re_ratio'] = B8 / (B6 + 1e-6)  # NIR/Red Edge
features['re_ndvi'] = (B8A - B5) / (B8A + B5 + 1e-6)  # Red Edge NDVI

# Banda individual (captura ruido óptico)
features['blue_median'] = B2
features['red_median'] = B4
features['nir_median'] = B8
```

### Texturas GLCM (Sentinel-2)

```python
from skimage.feature import greycomatrix, greycoprops

# Calcular GLCM en banda NDVI o Red Edge
ndvi_int = ((features['ndvi'] + 1) * 127).astype(np.uint8)  # Escalar a 0-255

# GLCM: distancia=1, ángulos=[0,45,90,135]
glcm = greycomatrix(ndvi_int, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4])

# Propiedades de textura (promediar ángulos)
features['texture_contrast'] = greycoprops(glcm, 'contrast').mean()
features['texture_dissimilarity'] = greycoprops(glcm, 'dissimilarity').mean()
features['texture_homogeneity'] = greycoprops(glcm, 'homogeneity').mean()
features['texture_asm'] = greycoprops(glcm, 'ASM').mean()  # Angular Second Moment
features['texture_entropy'] = greycoprops(glcm, 'entropy').mean()

# Interpretación:
# - contrast alto = variabilidad espacial (bosque heterogéneo)
# - homogeneity alto = uniformidad (plantación, sabana)
# - entropy alto = complejidad (estructural)
```

### Sentinel-1 SAR

```python
# VV: vertically polarized transmit, vertical receive (penetra suelo)
# VH: vertical transmit, horizontal receive (sensible a vegetación)
VV = S1['VV']
VH = S1['VH']

features['vv_median'] = VV
features['vh_median'] = VH
features['vv_vh_ratio'] = VV / (VH + 1e-6)
features['vv_vh_sum'] = VV + VH  # Total backscatter (biomasa proxy)
features['vv_vh_diff'] = VV - VH

# Importante: SAR es muy sensible a ángulo de incidencia, humedad suelo, artefactos
# Requiere normalización por ángulo de incidencia (slant_range_time en metadata)
```

### Topografía (SRTM/TanDEM-X)

```python
from scipy.ndimage import sobel, gaussian_filter

dem = elevation_raster  # DEM en metros

# Slope (grados)
slope_x = sobel(dem, axis=0)
slope_y = sobel(dem, axis=1)
slope_rad = np.arctan(np.sqrt(slope_x**2 + slope_y**2))
features['slope'] = np.degrees(slope_rad)

# Aspect (dirección: 0-360°)
aspect = np.degrees(np.arctan2(slope_y, slope_x))
features['aspect'] = np.where(aspect < 0, aspect + 360, aspect)

# Curvatura (cambio de pendiente)
features['curvature'] = gaussian_filter(slope_rad, sigma=2)

# Elevation
features['elevation'] = dem

# Topographic Position Index (TPI): altura relativa a vecinos
dem_smooth = gaussian_filter(dem, sigma=100)  # Filtro de contexto regional
features['tpi'] = dem - dem_smooth

# Noteworthy: slope > 15° debe ser excluido antes de ML (outliers)
```

### Selección Final de Features

```python
# No incluir:
# - Coordenadas (lat, lon) → causa overfitting espacial
# - ID o índices
# - Variables altamente colineales (e.g., NDVI + EVI juntos)

# Incluir:
key_features = [
    'rh50', 'rh25', 'rh75', 'rh_amplitude', 'rh_uniformity',  # GEDI core
    'ndvi', 'ndre', 're_ratio', 'evi',  # Sentinel-2 spectral
    'texture_contrast', 'texture_entropy',  # Texturas
    'vv_vh_ratio', 'vv_vh_sum',  # Sentinel-1 SAR
    'slope', 'elevation', 'tpi',  # Topografía
]

X = df[key_features].values  # n_samples × n_features
y = df['agbd'].values  # target (biomasa)
```

---

## Train/Val/Test Splitting

### ❌ INCORRECTO: Random Split (NUNCA usar en datos espaciales)

```python
from sklearn.model_selection import train_test_split

# Esto causa data leakage! Puntos cercanos en diferentes sets.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
# RESULTADO: RMSE inflado artificialmente bajo (overfitting sin detectar)
```

### ✅ CORRECTO: Particionamiento Geográfico

```python
# Estrategia 1: División por región/país
# (requiere tabla de atributos territoriales)

regions = df['region'].unique()  # ['Amazonas', 'Pará', 'Rondônia', ...]

# Train: 2 regiones amplias
train_mask = df['region'].isin(['Amazonas', 'Pará'])
X_train, y_train = X[train_mask], y[train_mask]

# Val: 1 región
val_mask = df['region'].isin(['Rondônia'])
X_val, y_val = X[val_mask], y[val_mask]

# Test: región completamente nueva
test_mask = df['region'].isin(['Mato Grosso'])
X_test, y_test = X[test_mask], y[test_mask]

print(f"Train: {X_train.shape[0]} samples, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")
# Output: Train: 45000, Val: 12000, Test: 8000 (típico)
```

### ✅ CORRECTO: Validación Cruzada K-Fold Geográfica

```python
from sklearn.model_selection import KFold
import numpy as np

def spatial_k_fold_split(X, y, coords, k=5):
    """
    K-fold donde cada fold agrupa puntos cercanos.
    coords: array (n, 2) con [lon, lat]
    """
    from sklearn.cluster import KMeans
    
    # Cluster espacial k-means
    kmeans = KMeans(n_clusters=k, random_state=42)
    clusters = kmeans.fit_predict(coords)
    
    folds = []
    for fold_idx in range(k):
        val_idx = np.where(clusters == fold_idx)[0]
        train_idx = np.where(clusters != fold_idx)[0]
        folds.append((train_idx, val_idx))
    
    return folds

# Uso
coords = df[['lon', 'lat']].values
folds = spatial_k_fold_split(X, y, coords, k=5)

for fold_idx, (train_idx, val_idx) in enumerate(folds):
    X_train_fold, y_train_fold = X[train_idx], y[train_idx]
    X_val_fold, y_val_fold = X[val_idx], y[val_idx]
    
    print(f"Fold {fold_idx}: train={len(train_idx)}, val={len(val_idx)}")
```

---

## Tuning de Hiperparámetros

### Random Forest: Búsqueda Random

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV

param_dist = {
    'n_estimators': [100, 200, 300, 500],  # Número de árboles
    'max_depth': [8, 12, 16, 20, None],  # Profundidad máxima
    'min_samples_split': [5, 10, 20],  # Muestras mín para dividir
    'min_samples_leaf': [2, 4, 8],  # Muestras mín en hoja
    'max_features': ['sqrt', 'log2'],  # Características por split
    'bootstrap': [True],  # Muestreo con reemplazo
    'n_jobs': [-1],  # Paralelizar
}

rf = RandomForestRegressor(random_state=42)

search = RandomizedSearchCV(
    rf,
    param_distributions=param_dist,
    n_iter=20,  # 20 combinaciones aleatorias
    cv=5,  # 5-fold CV
    scoring='neg_mean_squared_error',
    n_jobs=-1,
    verbose=1
)

search.fit(X_train, y_train)
print(f"Best params: {search.best_params_}")
print(f"Best CV RMSE: {np.sqrt(-search.best_score_):.2f} Mg/ha")

# Reentrenar con best params
rf_final = RandomForestRegressor(**search.best_params_, random_state=42)
rf_final.fit(X_train, y_train)
```

### XGBoost: Bayesian Optimization con Optuna

```python
import xgboost as xgb
import optuna
from optuna.samplers import TPESampler

def objective(trial):
    """Función objetivo para Optuna"""
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0, 10),
        'random_state': 42,
        'n_jobs': -1,
    }
    
    # XGBoost con early stopping
    xgb_model = xgb.XGBRegressor(**params)
    
    # Validación cruzada
    from sklearn.model_selection import cross_val_score
    cv_scores = cross_val_score(
        xgb_model, X_train, y_train,
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )
    rmse = np.sqrt(-cv_scores.mean())
    
    return rmse

# Optimización Bayesiana
sampler = TPESampler(seed=42)
study = optuna.create_study(sampler=sampler, direction='minimize')
study.optimize(objective, n_trials=50, show_progress_bar=True)

print(f"Best RMSE: {study.best_value:.2f} Mg/ha")
print(f"Best params: {study.best_params}")

# Reentrenar con best params
xgb_final = xgb.XGBRegressor(**study.best_params, random_state=42)
xgb_final.fit(X_train, y_train)
```

### LightGBM: Tuning Rápido

```python
import lightgbm as lgb
from sklearn.model_selection import cross_val_score

lgb_params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'max_depth': 10,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'verbose': -1,
}

lgb_model = lgb.LGBMRegressor(**lgb_params, n_estimators=200, random_state=42)

# Quick CV
cv_scores = cross_val_score(
    lgb_model, X_train, y_train,
    cv=5,
    scoring='neg_mean_squared_error',
    n_jobs=-1
)
print(f"CV RMSE: {np.sqrt(-cv_scores.mean()):.2f} Mg/ha")

# Entrenar
lgb_model.fit(X_train, y_train)
```

---

## Evaluación y Validación

### Métricas Estándar

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Predicción en test set
y_pred = model.predict(X_test)
y_test_array = np.array(y_test)

# Métricas
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
rrmse = 100 * rmse / y_test_array.mean()  # Relativo (%)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
bias = (y_pred - y_test_array).mean()

print(f"RMSE: {rmse:.2f} Mg/ha")
print(f"RRMSE: {rrmse:.1f}%")
print(f"MAE: {mae:.2f} Mg/ha")
print(f"R²: {r2:.3f}")
print(f"Bias (sesgo): {bias:.2f} Mg/ha (>0 = sobrestimación)")
```

### Validación por Estratos de Biomasa

```python
# Crucial para comunicar limitaciones
biomass_ranges = [
    (0, 100, 'Bajo'),
    (100, 200, 'Medio'),
    (200, 350, 'Alto')
]

results = []
for min_agbd, max_agbd, label in biomass_ranges:
    mask = (y_test_array >= min_agbd) & (y_test_array < max_agbd)
    y_test_stratum = y_test_array[mask]
    y_pred_stratum = y_pred[mask]
    
    if len(y_test_stratum) > 10:  # Al menos 10 muestras
        rmse_s = np.sqrt(mean_squared_error(y_test_stratum, y_pred_stratum))
        rrmse_s = 100 * rmse_s / y_test_stratum.mean()
        r2_s = r2_score(y_test_stratum, y_pred_stratum)
        
        results.append({
            'biomass_range': label,
            'n_samples': len(y_test_stratum),
            'rmse_mgh': rmse_s,
            'rrmse_%': rrmse_s,
            'r2': r2_s,
        })
        
        print(f"{label} ({min_agbd}-{max_agbd} Mg/ha): "
              f"RMSE={rmse_s:.1f} ({rrmse_s:.1f}%), R²={r2_s:.3f}, N={len(y_test_stratum)}")
```

### Plots de Validación

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. Predicted vs Observed
axes[0, 0].scatter(y_test, y_pred, alpha=0.5, s=10)
min_val, max_val = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
axes[0, 0].plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='1:1 line')
axes[0, 0].set_xlabel('Observado (Mg/ha)')
axes[0, 0].set_ylabel('Predicho (Mg/ha)')
axes[0, 0].set_title(f'Predicted vs Observed (R²={r2:.3f})')
axes[0, 0].legend()

# 2. Residuales vs Predichos
residuals = y_test - y_pred
axes[0, 1].scatter(y_pred, residuals, alpha=0.5, s=10)
axes[0, 1].axhline(y=0, color='r', linestyle='--')
axes[0, 1].set_xlabel('Predicho (Mg/ha)')
axes[0, 1].set_ylabel('Residual (Observado - Predicho)')
axes[0, 1].set_title('Residual Plot')

# 3. Distribución de residuales
axes[1, 0].hist(residuals, bins=50, edgecolor='black')
axes[1, 0].axvline(x=0, color='r', linestyle='--', lw=2)
axes[1, 0].set_xlabel('Residual (Mg/ha)')
axes[1, 0].set_title(f'Residual Distribution (µ={residuals.mean():.2f})')

# 4. Q-Q plot (normalidad de residuales)
from scipy import stats
stats.probplot(residuals, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot')

plt.tight_layout()
plt.savefig('validation_plots.png', dpi=150)
plt.show()
```

---

## Random Forest: Detalles

### Ventajas
- **Interpretabilidad**: Feature importance clara (Gini, MDI)
- **Velocidad**: Entrenamiento rápido (< 1 min típico)
- **Datos faltantes**: Maneja NaN automáticamente
- **No necesita normalización**: Invariante a escala
- **Exploración**: Ideal para entender relaciones rápidamente

### Desventajas
- **Exactitud**: Generalmente inferior a XGBoost/LightGBM (~5-15% RMSE más alto)
- **Sobreajuste**: Tiende a overfitting con features muy ruidosas
- **Extrapolación**: No predice bien fuera del rango de entrenamiento

### Hiperparámetros clave
- **max_depth**: 8-16 (profundidad máxima). Limitar evita overfitting.
- **min_samples_leaf**: 2-8. Número mín de muestras en hoja. Mayor = más simple.
- **n_estimators**: 100-500 (más no siempre mejor, retornos decrecientes)

### Código completo RF

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle

# Normalizar features (opcional pero recomendado)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Entrenar
rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=4,
    min_samples_split=10,
    max_features='sqrt',
    n_jobs=-1,
    random_state=42,
    verbose=1
)
rf.fit(X_train_scaled, y_train)

# Evaluar
y_val_pred = rf.predict(X_val_scaled)
val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
print(f"Validation RMSE: {val_rmse:.2f} Mg/ha")

# Feature importance
importance = rf.feature_importances_
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importance
}).sort_values('importance', ascending=False)
print(importance_df.head(10))

# Guardar
with open('rf_model.pkl', 'wb') as f:
    pickle.dump(rf, f)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
```

---

## XGBoost: Detalles

### Ventajas
- **Exactitud**: Mejor RMSE que RF, especialmente en datos grandes
- **Velocidad**: Entrenamiento rápido, optimizaciones internas (hardware-aware)
- **Regularización**: Control fino de overfitting (shrinkage, tree pruning)
- **Interpretabilidad**: SHAP values para explicabilidad local
- **Robustez**: Maneja valores faltantes, outliers mejor

### Desventajas
- **Hiperparámetros**: Muchos, requiere ajuste cuidadoso
- **Complejidad**: Más difícil de debuggear que RF

### Hiperparámetros clave
- **learning_rate** (eta): 0.01-0.3. Menor = más conservador, necesita más árboles.
- **max_depth**: 3-15. XGBoost típicamente 5-12 vs RF 8-16.
- **subsample**: 0.5-1.0. Fracción de muestras por árbol.
- **colsample_bytree**: 0.5-1.0. Fracción de features por árbol.
- **min_child_weight**: 1-10. Suma de pesos mín en hoja (como min_samples_leaf).
- **gamma**: 0-10. Reducción mín de pérdida para splits (regularización).

### Código completo XGBoost

```python
import xgboost as xgb
from xgboost import DMatrix, XGBRegressor

# Crear datasets de XGBoost (más eficiente para grandes datos)
dtrain = DMatrix(X_train, label=y_train)
dval = DMatrix(X_val, label=y_val)
dtest = DMatrix(X_test, label=y_test)

params = {
    'objective': 'reg:squarederror',
    'metric': 'rmse',
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 5,
    'gamma': 1.0,
    'reg_alpha': 0.1,  # L1 regularization
    'reg_lambda': 1.0,  # L2 regularization
    'seed': 42,
}

# Early stopping
evals = [(dtrain, 'train'), (dval, 'eval')]
evals_result = {}

xgb_model = xgb.train(
    params,
    dtrain,
    num_boost_round=1000,
    evals=evals,
    evals_result=evals_result,
    early_stopping_rounds=50,
    verbose_eval=False,
)

# Evaluar
y_test_pred = xgb_model.predict(dtest)
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
print(f"Test RMSE: {test_rmse:.2f} Mg/ha")

# Feature importance
importance_xgb = xgb_model.get_score(importance_type='weight')
sorted_imp = sorted(importance_xgb.items(), key=lambda x: x[1], reverse=True)
print("Top features:", sorted_imp[:10])

# Guardar
xgb_model.save_model('xgb_model.json')
```

---

## LightGBM: Detalles

### Ventajas
- **Velocidad**: MUCHO más rápido que XGBoost en datos grandes (millones de muestras)
- **Memoria**: Consumo bajo, ideal para datasets masivos
- **Exactitud**: Comparable o mejor a XGBoost
- **Flexible**: Maneja clasificación, regresión, ranking

### Desventajas
- **Overfitting**: Más propenso a sobreajuste que XGBoost (requiere validación cuidadosa)
- **Datos pequeños**: No es ventajoso si N < 10k samples

### Cuándo usar
- **RF**: Exploración rápida, datasets < 100k
- **XGBoost**: Balance exactitud-velocidad, datos medianos (100k-1M)
- **LightGBM**: Velocidad máxima, datos masivos (>1M), GEE pipelines

### Código completo LightGBM

```python
import lightgbm as lgb

# Dataset LightGBM (más eficiente)
train_data = lgb.Dataset(X_train, label=y_train)
val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'max_depth': 10,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 5,
    'verbose': -1,
}

# Early stopping
callbacks = [
    lgb.early_stopping(50),
    lgb.log_evaluation(period=0),
]

lgb_model = lgb.train(
    params,
    train_data,
    num_boost_round=1000,
    valid_sets=[val_data],
    callbacks=callbacks,
)

# Evaluar
y_test_pred = lgb_model.predict(X_test)
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
print(f"Test RMSE: {test_rmse:.2f} Mg/ha")

# Guardar
lgb_model.save_model('lgb_model.txt')
```

---

## Comparación RF vs XGBoost vs LightGBM

### Benchmark Típico (Datos GEDI Amazonia, N=50k)

| Métrica | Random Forest | XGBoost | LightGBM |
|---------|---------------|---------|----------|
| RMSE (Mg/ha) | 18.2 | 16.5 | 16.3 |
| Training time | 12 sec | 8 sec | 2 sec |
| Memory (GB) | 0.8 | 1.2 | 0.5 |
| Feature importance | Clear | SHAP flexible | Built-in |
| Hyperparameter tuning | Fácil | Medio | Difícil |
| Overfitting risk | Bajo | Medio | Alto |

### Recomendación por Caso de Uso

**Exploración rápida (seminario, idea inicial)**:
→ Random Forest (fácil, interpretable)

**Producción, exactitud crítica**:
→ XGBoost (balance)

**Datos masivos, velocidad máxima**:
→ LightGBM (GEE pipeline)

**Análisis de sensibilidad, incertidumbre**:
→ Ensemble (RF + XGBoost, promediar predicciones)

