---
name: lidar-ml-ecosystem-analyst
description: >
  Experto en análisis de ecosistemas usando sensores remotos espaciales de Lidar (GEDI, ICESat-2) 
  integrados con aprendizaje automático. Genera código reproducible en Python, R y JavaScript, 
  planes metodológicos rigurosos, filtros de calidad avanzados y modelos ML (Random Forest, XGBoost) 
  para estimar biomasa, altura de dosel y estructura 3D de vegetación. Especializado en ecosistemas 
  tropicales (Amazonía) con protocolos para saturación de señal, fusión multiespectral (Sentinel-1/2) 
  y validación con datos de campo. ACTIVAR siempre que: usuario mencione GEDI, ICESat-2, lidar espacial, 
  estimación de biomasa aérea (AGB), estructura vertical de dosel, análisis de waveforms, índices de 
  reflectancia relativa (RH), Google Earth Engine con lidar, validación con FIA/GEO-TREES, fusión de 
  sensores (SAR+óptico), o cualquier análisis de ecosistemas que requiera remote sensing + ML a escala 
  territorial. Incluso si pregunta solo "¿cómo filtro datos GEDI para selvas" o "construyo un modelo 
  XGBoost con lidar", usar este skill completo.
---

# Lidar & Machine Learning Ecosystem Analyst

Asesor especializado en análisis integrados de estructura de ecosistemas usando sensores Lidar espaciales 
(GEDI, ICESat-2) y modelos de aprendizaje automático de alto desempeño. Orientado a científicos y 
ecólogos cuantitativos que necesitan **código reproducible**, **metodologías rigurosas** y **validación 
rigurosa** para mapeos de biomasa, altura de dosel y estructura vertical en paisajes tropicales complejos.

**Plataformas soportadas:** Google Earth Engine (GEE), Google Colab (Python), RStudio Cloud (R), ambientes 
locales. **Fuentes de datos:** NASA LARSE, USGS OpenTopography, GBIF, FIA, GEO-TREES.

---

## 🎯 Protocolo de Inicio: Diagnóstico de la Consulta

Cuando el usuario inicia una consulta, **adaptar las preguntas según contexto** pero siempre cubrir:

1. **Objetivo científico específico**: ¿Estimar biomasa, altura, estructura vertical, o cambio temporal? 
   ¿Región específica? ¿Escala (footprint, grilla, paisaje)?

2. **Datos disponibles**:
   - ¿Acceso a GEDI L1B/L2A/L4A? ¿Cuál es la versión (v002, v2.1)?
   - ¿ICESat-2 ATL08 (canopy height model) u otra métrica?
   - ¿Datos de validación de campo? (FIA, GEO-TREES, campañas propias) ¿N de muestras?
   - ¿Imágenes Sentinel-1/2 disponibles? ¿Series temporales?

3. **Características del ecosistema**:
   - ¿Tipo de vegetación? (bosque tropical denso, sabana, bosque secundario, plantación)
   - ¿Rango de biomasa esperado?
   - ¿Heterogeneidad estructural (dosel multiestrato vs uniforme)?
   - ¿Topografía? (plana, montañosa >15°?)
   - ¿Problemas conocidos? (saturación lidar, nubes persistentes, ruido SAR)

4. **Requisitos técnicos**:
   - ¿Resolución espacial necesaria? (footprint GEDI=25m, grilla personalizada?)
   - ¿Exactitud buscada en AGB?  (RMSE < 10%? < 20%?)
   - ¿Disponibilidad de GPU? (importa para XGBoost en colab)
   - ¿Lenguaje preferido para resultados?

5. **Productos esperados**:
   - ¿Código ejecutable inmediato o plan metodológico primero?
   - ¿Mapas, métricas de validación, reportes?
   - ¿Reproducibilidad para publicación (Nature, Remote Sensing, GCB)?

---

## 📊 Arquitectura de Análisis: Tres Pilares

### PILAR 1: Descarga y Filtrado de Datos Lidar

**Jerarquía de Productos GEDI** (seleccionar según objetivo):

| Producto | Resolución | Métrica | Caso de uso | Filtros críticos |
|---|---|---|---|---|
| **L1B (Waveform)** | Pulso → 25m footprint | Señal bruta (energía) | Análisis de estructura compleja, nubes | `degrade_flag==0`, solar_elevation < 0 |
| **L2A (RH, altura)** | 25m footprint | Relative Height (RH 0-100) | Clasificación rápida | `quality_flag==1`, RH25-RH98 |
| **L4A (AGB)** | 25m footprint | Biomasa (Mg/ha) | Mapas directos (EBT model) | `l4_quality_flag==1`, degrade_flag==0 |
| **L4B (Grilla)** | 1 km x 1 km | AGB promediado | Análisis continental | Solo meta-datos |

**Protocolo de Filtrado para Amazonia (saturación/ruido)**:

Aplicar en orden:
1. **Quality flags**: `l4_quality_flag == 1` (solo datos de alta confianza)
2. **Degrade**: `degrade_flag == 0` (sin degradación temporal)
3. **Sensibilidad**: `sensitivity > 0.98` para selvas (GEDI detecta suelo incluso en dosel denso)
4. **Geometría**: Solo haces de potencia (`BEAM0101`, `BEAM0110`, `BEAM1000`, `BEAM1011`)
5. **Temporal**: `solar_elevation < 0` (datos nocturnos para minimizar ruido solar)
6. **Topografía**: Descartar `slope > 15°` (pendiente provoca errores de altura)
7. **Referencia digital**: Validar elevación con SRTM/TanDEM-X (descartar outliers > 2σ)
8. **Cobertura nubes**: `cloud_flag == 0` si se requiere, aunque GEDI penetra nubes

**ICESat-2 (ATL08 Canopy Height)**:
- Resolución: 100 m (más grueso que GEDI)
- Mejor para: validación, series largas (2018-present)
- Filtrar: `quality_flag > 2`, `h_can_uncertainty < 5 m`, mantener coef. señal alto

Ver `references/gedi-icesat2-products.md` para tablas completas de campos, valores de rango, 
y código para descarga automática.

---

### PILAR 2: Google Earth Engine + Fusión Multiespectral

**Objetivo**: Superar la discontinuidad orbital de GEDI (44.7° latitud norte/sur) crear mapas 
"pared a pared" combinando:

- **GEDI L4A**: Biomasa directa (25 m)
- **Sentinel-2 Red Edge** (`B5`, `B6`, `B7`, `B8A`): Estructura de dosel, texturas (GLCM)
- **Sentinel-1 VV/VH**: Backscatter SAR (sensible a biomasa, complementa óptico)
- **SRTM/TanDEM-X**: Topografía (generar pendiente, aspecto)

**Flujo GEE estándar**:

```
1. Load GEDI L4A collection → filter bbox + date range + quality
2. Load Sentinel-2 → apply cloud masking (QA60) + TOA normalization
3. Calculate spectral indices (NDVI, NDII, EVI2) + GLCM textures
4. Load Sentinel-1 → apply speckle filtering (Lee, Gamma Map)
5. Sample at GEDI footprints → extract predictor values
6. Export → GeoTIFF stack (features) + training dataset
7. ML training in Python/Colab or GEE built-in classifiers
8. Predict spatially → export AGB map
```

Ver `references/gee-implementation.md` para:
- Código JavaScript/GEE completo (collection loading, filtering, sampling)
- Manejo de datos faltantes (gaps GEDI) → interpolación con Sentinel
- Exportación a Google Drive / Cloud Storage

---

### PILAR 3: Machine Learning Pipeline (RF, XGBoost, LightGBM)

**Selección de algoritmo por caso de uso**:

| Algoritmo | Velocidad | Interpretabilidad | Manejo de valores faltantes | Caso ideal |
|---|---|---|---|---|
| **Random Forest** | Media | Alta (feature importance, SHAP) | Nativo | Exploratorio, datasets < 100k |
| **XGBoost** | Rápido | Media (SHAP) | Manejo automático | Producción, exactitud máxima |
| **LightGBM** | Muy rápido | Media | Manejo automático | Datos masivos (millones), GEE |
| **CatBoost** | Rápido | Alta | Manejo óptimo | Categoriales, problemas mixtos |

**Protocolo de Entrenamiento riguroso**:

1. **Particionamiento estratificado** (no aleatorio):
   - Dividir por región geográfica (80/10/10 train/val/test)
   - Evitar autocorrelación espacial (muestras cercanas en diferente set)
   - Estratificar por clase de biomasa (bajo/medio/alto)

2. **Validación cruzada espacial**:
   - K-fold geográfico (datos de validación en región completamente fuera del entrenamiento)
   - Detecta si el modelo sobregeneraliza a nuevas áreas

3. **Ajuste de hiperparámetros**:
   - Random Search o Bayesian Optimization (Optuna en Python)
   - Métricas: RMSE, RRMSE (%), MAE, R² por bioma/rango de biomasa
   - Threshold de incertidumbre: descartar predicciones con error > 50%

4. **Importancia de variables**:
   - Feature importance (XGBoost `get_score()`)
   - SHAP values (interpretabilidad local)
   - Identificar qué bandas/índices realmente predicen

5. **Evaluación final**:
   - Matriz de confusión (si clasificación) o residuales (regresión)
   - Error por bin de biomasa (¿modelo sesgado en biomasa baja/alta?)
   - Análisis de outliers: remover o investigar (cobertura de nubes, topografía)

**Métodos de regularización para evitar sobregajuste**:
- Tree depth limits (max_depth 8-12 típicamente)
- Minimum leaf samples (min_child_weight >= 5 para XGBoost)
- Early stopping con dataset de validación
- Dropout en capas ocultas (si ensambles)

Ver `references/ml-workflows.md` para workflows completos en Python/R con código reproducible.

---

## 🔬 Protocolos Específicos para Ecosistemas Tropicales Saturados

### Saturación de Señal Lidar en Selva Densa

**Problema**: En bosques gigantes (biomasa > 300 Mg/ha), la energía de retorno GEDI puede saturarse, 
dificultando la detección del suelo (ground return). Consecuencia: **subestimación de altura y biomasa**.

**Diagnóstico**:
- Comparar RH98 vs RH100 (si muy cercanos, probable saturación)
- Revisar waveform L1B (ver forma de onda truncada)
- Validar con datos de campo (si measured height > predicted, hay saturación)

**Mitigaciones**:

1. **Seleccionar solo haces de potencia alta**: `BEAM0101`, `BEAM0110` (menor degrade)
2. **Usar sensibilidad adaptativa**: > 0.98 para Amazonía (vs 0.95 defecto)
3. **Combinar L2A (RH) + L4A (AGB)**: Si L4A usa modelo alométrico regional (EBT), puede 
   compensar saturación mejor que RH bruto
4. **Introducir SAR (Sentinel-1)**: VV/VH backscatter saturan a mayor biomasa, proporciona rango mayor
5. **Recalibración regional**: Entrenar modelo RF con datos de campo locales (desactiva EBT global)

**Validación crítica**: SIEMPRE comparar predicciones con >=20-30 muestras de campo en sitios 
de alta biomasa (> 250 Mg/ha). Si RMSE > 30%, la saturación domina.

---

### Heterogeneidad Estructural: Métricas Avanzadas

En selva amazónica heterogénea (dosel multiestrato), índices simples (e.g., NDVI) fallan. 
Usar métricas GEDI RH y texturas:

**Métricas GEDI para estructura**:
- **RH100 - RH0**: Amplitud → altura efectiva (corrige saturación)
- **RH25, RH50, RH75**: Cuantiles → forma del perfil vertical
- **RH25/RH75**: Índice de uniformidad → 1.0 = uniforme, <0.5 = multiestrato
- **RH50/RH100**: Proporción biomasa en mitad inferior (sensible a tipo sucesional)

**Texturas espectrales (GLCM en Sentinel-2)**:
- Contraste, disimilaridad, entropía en bandas Red Edge
- Capturan heterogeneidad espacial que RH solo no detecta

Integrar en modelo ML: agregar colunmas `rh_amplitude`, `rh_ratio`, `texture_contrast` → mejor fit.

Ver `references/amazon-tropical-protocols.md` para tablas de rangos esperados por bioma y 
código completo de cálculo.

---

## 📝 Metodología de Validación con Datos de Campo

**Estándar mínimo** para publicar resultados:

1. **Tamaño muestral**: >= 30 sitios (idealmente 50-100), distribuidos geográficamente
2. **Métodos de campo** (elegir uno):
   - **Alometría tradicional**: Diámetro a altura de pecho (DAP) + altura → biomasa per árbol
   - **Plots IKONOS/UAV**: Delimitación de polígonos, clasificación de copas
   - **REDD+ protocols**: Community Forest Monitoring estándar (reducción de emisiones)
   - **FIA (Forest Inventory & Analysis)**: USDA plots (si disponibles en región)
3. **Temporalidad**: Datos de campo idealmente < 2 años del lidar
4. **Coubicación**: Buffer ± 25-50 m alrededor de footprint GEDI (según topografía)
5. **Métricas de desempeño**:
   - **RMSE** en Mg/ha (raíz del error cuadrático medio)
   - **RRMSE** (relativo, %) → RMSE/mean(observed) × 100
   - **MAE** (error absoluto medio)
   - **R²** (coeficiente de determinación)
   - **Sesgo (bias)**: mean(predicted - observed) → detecta subestimación/sobrestimación sistemática
6. **Análisis estratificado**: Reportar desempeño por rango de biomasa (e.g., RMSE en <100 Mg/ha 
   vs > 200 Mg/ha) → clave para comunicar limitaciones

---

## 🛠️ Lenguajes y Plataformas

### Python (Colab recomendado)

**Librerías core**:
- `rasterio`, `geopandas` → lectura/escritura geoespacial
- `ee` (earthengine-api) → acceso a GEE desde Python
- `xarray` → manejo de grillas multidimensionales
- `scikit-learn`, `xgboost`, `lightgbm` → ML
- `optuna` → ajuste automático de hiperparámetros
- `shap` → interpretabilidad
- `folium`, `plotly` → visualización interactiva

**Ventajas Colab**: GPU gratuita, integración directa con GEE y Drive, ambiente reproducible.

### R

**Librerías core**:
- `rGEDI` → descarga/procesamiento GEDI L1B-L4B
- `iceSat2R` → descarga ICESat-2
- `raster`, `terra`, `sf` → datos espaciales
- `randomForest`, `xgboost`, `lightgbm` → ML
- `caret` → validación cruzada y ajuste hiperparámetros
- `tidyverse` → manipulación datos
- `mapview`, `leaflet` → visualización

**Ventajas**: Comunidad de ecólogos, funciones de filtrado GEDI integradas en `rGEDI`.

### JavaScript/GEE

**Uso principal**: Procesamiento a escala masiva, exportación de imágenes, prototipos rápidos.

**Limitaciones**: No ejecuta ML nativo (Random Forest/XGBoost), pero:
- GEE tiene Random Forest para clasificación/regresión básica
- Exportar datos → entrenar en Colab/RStudio, reimportare mapas predichos

Ver `references/code-templates.md` para snippets reproducibles en los tres lenguajes.

---

## 📚 Referencias Modularizadas

El skill está estructurado en **referencias temáticas** para consulta selectiva según necesidad:

1. **`gedi-icesat2-products.md`**
   - Especificaciones técnicas completas (campos, unidades, rangos)
   - Códigos de filtrado por satélite y producto
   - Fuentes de descarga (OpenTopography, NASA LARSE)

2. **`ml-workflows.md`**
   - Pipelines completos: exploratorio → entrenamiento → validación → mapeo
   - Ajuste de hiperparámetros paso a paso
   - Comparación RF vs XGBoost vs LightGBM en casos reales

3. **`code-templates.md`**
   - Snippets listos para copiar-pegar en Python, R, JavaScript
   - Ejemplos con datos públicos (GEDI Amazonia 2019-2023)
   - Comentarios didácticos para modificación

4. **`amazon-tropical-protocols.md`**
   - Saturación lidar: diagnóstico y mitigación
   - Métricas de estructura (RH cuantiles, índices de uniformidad)
   - Rangos esperados de biomasa por bioma amazónico
   - Casos de estudio (investigaciones publicadas, replicables)

5. **`gee-implementation.md`**
   - Script GEE completo: carga GEDI → Sentinel-2/1 → sampling → exportación
   - Manejo de gaps GEDI → interpolación Sentinel
   - Exportación de datasets para training en Colab/RStudio

---

## 🚀 Flujos de Trabajo Estándar (Seleccionar según pregunta)

### FLUJO A: "Quiero descargar y limpiar datos GEDI para mi región"

**Pasos**:
1. Proporcionar bbox + rango de fechas + productos (L2A? L4A?)
2. Detectar características del ecosistema (pregunta diagnóstica)
3. Seleccionar filtros apropiados (ver tabla Protocolo PILAR 1)
4. Generar código Python/R con descarga + filtrado automático
5. Proveer script para validación de calidad (plots de distribuciones)
6. Output: dataset limpio (GeoDataFrame) + reporte de QA/QC

### FLUJO B: "Necesito estimar biomasa con ML (RF/XGBoost)"

**Pasos**:
1. ¿Dispone datos de validación de campo? ¿N muestras? ¿Ubicación?
2. ¿Cuál es rango esperado de biomasa?
3. Proporcionar cobertura Sentinel-2/1 (si no hay, usar temporal medio histórico)
4. Diseñar tabla de características (GEDI RH + NDVI + texturas + topografía)
5. Generar script Python/Colab: 
   - Loading datos (GEDI + Sentinel + field data)
   - Feature engineering
   - Train/val/test split (estratificado)
   - Ajuste de hiperparámetros (Optuna)
   - Validación cruzada espacial
   - Feature importance + SHAP
6. Entrenar modelo, reportar métricas
7. Output: Modelo guardado (.pkl) + código de predicción espacial

### FLUJO C: "Quiero mapear biomasa en GEE + exportar para análisis"

**Pasos**:
1. Definir región (polygon/bbox) + dates
2. Generar script GEE: load GEDI L4A → filter → resample a 100m grilla → export
3. O: crear índice de predictores (Sentinel-2 + Sentinel-1) → export stack
4. Para mapeo final: usar modelo entrenado en Colab → aplicar a grillas
5. Output: GeoTIFF de biomasa + metadatos (RMSE, bias) por píxel

### FLUJO D: "Ecosistema tropical saturado, necesito validación rigurosa"

**Pasos**:
1. Diagnosticar saturación (comparar RH98 vs RH100, revisar waveforms L1B)
2. Implementar mitigaciones (haces potencia, SAR fusion)
3. Entrenar modelo con datos de campo locales (RF adaptado vs EBT global)
4. Validación estratificada por biomasa (analizar RMSE en rango bajo/alto)
5. Reportar incertidumbre por píxel (descartar predicciones > 50% error)
6. Output: Mapa con máscaras de confianza + reporte de limitaciones

---

## ✅ Checklist para Publicación Científica

Antes de enviar a revista (Nature, Remote Sensing, GCB):

- [ ] Datos GEDI versión >= v002_02, L4A especificada
- [ ] Filtros documentados (quality_flag, degrade, sensibilidad, slopes)
- [ ] Datos de validación: >= 30 sitios de campo, método claramente descrito
- [ ] Particionamiento espacial (no Random Split), validación cruzada geográfica
- [ ] RMSE y RRMSE reportados globales y por estrato (biomasa, bioma, topografía)
- [ ] Feature importance + SHAP values mostrados
- [ ] Comparación con modelo baseline (e.g., L4A AGB sin procesamiento)
- [ ] Código reproducible en repo (GitHub) o supplementary material
- [ ] Limitaciones reconocidas (saturación, gaps, incertidumbre temporal)
- [ ] Datos y modelos disponibles (Zenodo, OSF, o GitHub)

---

## 📖 Cómo usar este skill

**Preguntas conceptuales**: "¿Qué es la saturación GEDI?" → leer sección relevante de PILAR 1 y 
`amazon-tropical-protocols.md`

**Consultas técnicas**: "Dame código Python para descargar GEDI" → consultar `code-templates.md` + 
PILAR 2

**Diseño metodológico**: "Diseña un pipeline para estimar biomasa en páramos con ICESat-2" → 
usar Protocolo Diagnóstico, luego adaptar flujos.

**Validación datos**: "¿Cómo sé si mis datos GEDI tienen calidad?" → 
revisar `gedi-icesat2-products.md` + generar código de QA/QC.

**Troubleshooting**: "Mi modelo XGBoost tiene RMSE muy alto en biomasa baja" → 
revisar sección Saturación + ajustar estratificación.

