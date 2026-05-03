# GEDI & ICESat-2 Products: Especificaciones Técnicas y Filtros

## Tabla de Contenidos
- [GEDI Products Overview](#gedi-products-overview)
- [GEDI L2A: Relative Heights](#gedi-l2a-relative-heights)
- [GEDI L4A/L4B: Biomasa](#gedi-l4ab-biomasa)
- [ICESat-2 ATL08: Canopy Height](#icesat2-atl08-canopy-height)
- [Filtrado Multicapa por Ecosistema](#filtrado-multicapa-por-ecosistema)
- [Fuentes de Descarga](#fuentes-de-descarga)

---

## GEDI Products Overview

GEDI (Global Ecosystem Dynamics Investigation) es un instrumento **Lidar de forma de onda completa** 
a bordo de la ISS. Orbita a 44.7°N/S (no cubre trópicos extremos). Lanza ~242 huellas/segundo en 
una banda de observación.

### Jerarquía de Productos GEDI

```
L0 (Raw) → L1B (Waveform) → L2A (Relative Heights) → L2B (Canopy indices) 
                                                   → L4A (Biomasa footprint)
                                                   → L4B (Biomasa grilla 1km)
```

**Datos públicos disponibles**:
- GEDI L1B, L2A, L2B, L4A: OpenTopography (full resolution)
- GEDI L4B: NASA LARSE (Goddard DAAC)
- **Versiones estables**: v002_02 (L2A/L2B), v2_1 (L4A v2, recomendado 2023+)

**Cobertura temporal**: Abril 2019 - Presente (datos históricos completos en OpenTopography)

---

## GEDI L2A: Relative Heights

**Resolución**: 25 m footprint (~21 m de diámetro real)
**Métrica principal**: RH (Relative Height) = altura relativa de retorno en forma de onda
**Rango**: RH0-RH100 (percentiles)

### Campos Críticos L2A

| Campo | Tipo | Rango | Descripción | Filtro recomendado |
|-------|------|-------|-------------|-------------------|
| `relative_h` | float[101] | 0-100 | Percentiles de altura relativa | RH25, RH50, RH75, RH98 directamente |
| `beam` | string | BEAM0101, BEAM0110, BEAM1000, BEAM1011 | Identificador de haz | SOLO haces potencia (excluir BEAM0011, BEAM0110 débil) |
| `quality_flag` | int | 0, 1 | Flag de calidad general (1=alta, 0=baja) | **quality_flag == 1** |
| `degrade_flag` | int | 0, 1 | Degradación temporal de pulso (0=bueno) | **degrade_flag == 0** |
| `sensitivity` | float | 0.0-1.0 | Probabilidad de detectar suelo (1.0=máxima) | **sensitivity > 0.98** Amazonia, >0.95 boreal |
| `cloud_flag` | int | 0, 1 | Presencia de nubes en trayectoria (1=nubes) | cloud_flag == 0 (opcional: GEDI penetra nubes) |
| `solar_elevation` | float | -180 a 180 | Ángulo solar (grados, <0=noche) | **solar_elevation < 0** (datos nocturnos, minimiza ruido) |
| `elev_highestreturn` | float | meters | Elevación del retorno más alto (dosel) | Comparar con SRTM para outliers |
| `elev_lowestmode` | float | meters | Elevación de modo más bajo (suelo estimado) | Validar con TanDEM-X |
| `delta_time` | float | seconds since 2018-01-01 | Timestamp GPS de adquisición | Filtrar por rango de fechas |
| `lat_lowestmode`, `lon_lowestmode` | float | degrees | Coordenadas del retorno más bajo | Para geolocalización |

### Rango Esperado de RH por Bioma

| Bioma | RH50 medio (m) | RH98 máximo (m) | RH50/RH100 (forma) | Notas |
|-------|---|---|---|---|
| Bosque tropical denso (Amazonia) | 20-30 | 35-50 | 0.4-0.6 | Multiestrato, sensible a saturación |
| Bosque secundario tropical | 15-25 | 25-35 | 0.5-0.7 | Menos saturación que primario |
| Sabana tropical | 8-15 | 15-25 | 0.6-0.8 | Estructura simple |
| Boreal (coníferas) | 15-25 | 25-35 | 0.5-0.7 | Menos dosel denso que trópico |
| Plantación (eucalipto) | 18-28 | 28-40 | 0.6-0.8 | Estructura regular |

**Interpretación RH**:
- **RH100**: Altura máxima detectada (aproxima altura de dosel, pero afectada por saturación)
- **RH50**: Altura mediana → proxy para biomasa bulk
- **RH50/RH100**: Índice de uniformidad (1.0=estructura uniforme, <0.5=multiestrato)

---

## GEDI L4A/L4B: Biomasa

**L4A**: 25 m footprint, biomasa estimada por modelo alométrico **EBT** (Evergreen Broadleaf Trees)
**L4B**: 1 km x 1 km grilla, promedio de L4A

### Campos Críticos L4A

| Campo | Tipo | Rango | Descripción | Filtro |
|-------|------|-------|-------------|--------|
| `agbd` | float | 0-400 Mg/ha | Estimación de biomasa aérea | Usar directamente |
| `agbd_std` | float | ±0-100 Mg/ha | Desviación estándar de estimación | Filtrar > 50% error: agbd_std/agbd > 0.5 |
| `l4_quality_flag` | int | 0, 1 | Quality flag específico L4A | **l4_quality_flag == 1** |
| `degrade_flag` | int | 0, 1 | Degradación (heredado de L2A) | **degrade_flag == 0** |
| `model_type` | int | 1, 2, 3, 4 | Modelo alométrico regional (ver tabla) | 2=Evergreen Broadleaf (Amazonia), 3=Deciduous |
| `sds_quality` | int | 0, 1 | SD algorithm quality flag | sds_quality == 1 |
| `selected_algorithm` | int | 1, 2 | Algoritmo de estimación | 1=preferido |
| `lat`, `lon` | float | degrees | Geolocalización | |

### Modelos Alométricos GEDI L4A (model_type)

| Valor | Bioma | Aplicable | Nota |
|-------|-------|-----------|------|
| 1 | Tropical Broadleaf (Genérico) | Pantropicales | Usado < frecuente |
| 2 | Evergreen Broadleaf (EBT) | **Amazonia, Congo, SE Asia** | Recomendado para trópicos húmedos |
| 3 | Deciduous Broadleaf | Trópicos secos, bosques caducifolios | Menos preciso para Amazonia |
| 4 | Coníferas | Boreal, templado | No aplicable trópicos |

**Precisión L4A EBT en Amazonia**:
- RMSE global: ~15-20 Mg/ha
- Para biomasa > 250 Mg/ha: RMSE puede alcanzar 25-30 Mg/ha (saturación)
- Para biomasa < 100 Mg/ha: RMSE ~ 10-12 Mg/ha

**Rango esperado AGB por sector Amazonia**:
- Tierra firme primaria: 180-280 Mg/ha
- Bosque secundario (>30 años): 120-180 Mg/ha
- Bosque secundario joven: 50-120 Mg/ha
- Cerrado/sabana: 20-60 Mg/ha

---

## ICESat-2 ATL08: Canopy Height

**Satélite**: Ice, Cloud, and land Elevation Satellite-2
**Instrumento**: ATLAS (Advanced Topographic Laser Altimeter System) de fotones (muy sensible)
**Resolución**: ~100 m footprint (diámetro mayor que GEDI)
**Cobertura**: 88°N a 88°S (cubre todo)
**Disponibilidad**: Noviembre 2018 - Presente

### Campos Críticos ATL08

| Campo | Rango | Descripción | Filtro recomendado |
|-------|-------|-------------|-------------------|
| `h_can` | 0-100 m | Altura de dosel estimada | Principal métrica |
| `h_can_uncertainty` | ±0-10 m | Incertidumbre de altura | **h_can_uncertainty < 5 m** |
| `quality_flag` | 0-4 | Calidad general (>2=buena) | **quality_flag > 2** |
| `signal_confidence` | 0-4 | Confianza en detección de señal | **signal_confidence > 2** |
| `msw_flag` | 0, 1 | Multiple scattering warning | 0=bueno |
| `terrain_flg` | 0-3 | Flag de terreno | Terreno plano=0, montañoso=3 (descartar >20°) |
| `delta_time` | seconds | Timestamp GPS | Filtrar fechas |

### Diferencias GEDI vs ICESat-2

| Aspecto | GEDI | ICESat-2 |
|--------|------|----------|
| Resolución | 25 m (excelente) | 100 m (buena) |
| Cobertura | 44.7°N/S | 88°N/S |
| Penetración dosel | Muy buena (waveform completa) | Buena (fotones) |
| Datos históricos | 2019-presente | 2018-presente |
| Uso ideal | Mapeo detallado, ML local | Validación, series largas |
| Saturación en biomasa alta | Moderada | Menor que GEDI |

**Estrategia combinada**: Usar GEDI L4A para entrenamiento ML (resolución), ICESat-2 para validación 
en regiones fuera de GEDI (>44.7°).

---

## Filtrado Multicapa por Ecosistema

### Protocolo Estándar: Amazonia Húmeda (Bosque Denso)

**Aplicar en orden**:

```
1. Seleccionar haces potencia:
   beam IN ['BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
   
2. Quality flags (GEDI L4A):
   l4_quality_flag == 1
   degrade_flag == 0
   sds_quality == 1
   
3. Sensibilidad (adaptada a Amazonia):
   sensitivity > 0.98
   
4. Error de estimación (biomasa):
   agbd_std / agbd < 0.50  (descartar incertidumbre > 50%)
   
5. Temporal (nocturnos):
   solar_elevation < 0
   
6. Cobertura de nubes (opcional, GEDI penetra):
   cloud_flag == 0  (si se requiere certeza)
   
7. Topografía (SRTM slope):
   slope < 15 grados
   
8. Validación de elevación (vs SRTM):
   |elev_lowestmode - SRTM_elevation| < 20 m
   
9. Rango biomasa esperado:
   50 <= agbd <= 300 Mg/ha  (descartar outliers extremos)
```

**Resultado**: Típicamente 60-75% de datos originales permanecen tras filtrado riguroso.

### Protocolo Adaptado: Bosque Tropical Saturado (Amazonia Gigante)

Si se sospecha **saturación** (RH98 ≈ RH100, o RH98 < 35 m):

```
1. Aplicar protocolo estándar (arriba)

2. Filtros adicionales anti-saturación:
   sensitivity > 0.995  (máximo sensibles)
   RH_amplitude = RH100 - RH0 > 15 m  (waveform con rango)
   
3. Usar solo L4A con model_type == 2 (EBT, Evergreen Broadleaf)
   NO usar L2A (RH) crudo sin post-procesamiento
   
4. En training ML posterior:
   - Incluir Sentinel-1 SAR (complementa saturación óptica)
   - Estratificar por rango de biomasa en CV
   - Reportar RMSE separadamente para biomasa > 250 Mg/ha
```

### Protocolo Boreal/Templado (sin saturación)

```
1. Aplicar protocolo estándar (sin paso 3: sensibilidad normal)

2. Especificaciones:
   sensitivity > 0.90  (boreal menos denso)
   solar_elevation > -30  (puede incluir crepúsculo)
   cloud_flag == 0  (nubes frecuentes, excluir)
   
3. Validar con SRTM > 50 m (relieve montañoso común)
```

---

## Fuentes de Descarga

### OpenTopography (Recomendado)

**URL**: https://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/GEDI/

**Acceso**: Requiere registro gratuito

**Productos disponibles**:
- GEDI L1B (waveforms crudos)
- GEDI L2A (RH, alturas)
- GEDI L2B (canopy indices)
- GEDI L4A (biomasa footprint)
- Histórico completo 2019-presente

**Ventaja**: Interfaz web simple, descarga rápida via FTP/HTTP

### NASA LARSE (Level 4 Data)

**URL**: https://larse.gsfc.nasa.gov/gedi/

**Productos**:
- GEDI L4A (análogo a OpenTopography)
- GEDI L4B (grilla 1 km)
- Documentación técnica oficial

**Formato**: HDF5 (requiere lectura especializada)

### Programático: Python (icepyx + earthaccess)

```python
# Descarga GEDI L4A con earthaccess + xarray
import earthaccess
from xarray import open_dataset

# Auth
earthaccess.login()

# Query GEDI L4A bbox + dates
results = earthaccess.search_data(
    short_name='GEDI04_B_02_002_05_R41000_MU',  # L4B v2
    bounding_box=(-75, -15, -60, 5),  # Amazonia
    temporal=('2020-01-01', '2023-12-31')
)

# Descargar
for file in earthaccess.get(results):
    ds = open_dataset(file, engine='h5netcdf')
    # Process...
```

### Programático: R (rGEDI)

```r
library(rGEDI)

# Auth EARTHDATA
set_earthdata_user("your_username", "your_password")

# Query y descarga L4A
gedi04b_data <- gedisimplify(
  gedilevel4b(
    filepath = ".",  # Local folder
    version = "002_05",
    degrade = 0,
    quality = 1,
    beam = c("BEAM0101", "BEAM0110", "BEAM1000", "BEAM1011"),
    bbox = c(-75, -15, -60, 5)  # lon_min, lat_min, lon_max, lat_max
  ),
  output = "all"
)

# Automático aplica algunos filtros (calidad, degrade)
# Pero debes aplicar sensitivity, topografía manually
```

### Google Earth Engine (via cloud)

```javascript
// Carga GEDI L4A en GEE
var gedi_col = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_V2_1')
  .filterBounds(aoi)
  .filterDate('2020-01-01', '2023-12-31');

// Aplica filtros
var gedi_filtered = gedi_col.map(function(img) {
  return img
    .updateMask(img.select('quality_flag').eq(1))
    .updateMask(img.select('degrade_flag').eq(0));
});

// Export
Export.image.toDrive({
  image: gedi_filtered.select('agbd'),
  scale: 30,
  maxPixels: 1e13
});
```

---

## Lectura de Archivos HDF5 GEDI

**Formato nativo**: HDF5 (Hierarchical Data Format 5)

### Python

```python
import h5py
import pandas as pd

# Abrir archivo GEDI L4A
with h5py.File('GEDI04_A_xyz.h5', 'r') as f:
    # Navega estructura
    print(f.keys())  # ['BEAM0101', 'BEAM0110', ...]
    
    # Leer datos de un beam
    beam = f['BEAM0101']
    agbd = beam['geolocation']['agbd'][:]  # numpy array
    agbd_std = beam['geolocation']['agbd_std'][:]
    quality = beam['geolocation']['quality_flag'][:]
    
    # Crear DataFrame
    df = pd.DataFrame({
        'agbd': agbd,
        'agbd_std': agbd_std,
        'quality': quality
    })
    
    # Filtrar
    df_clean = df[df['quality'] == 1]
```

### R

```r
library(rhdf5)
library(tidyverse)

# Abrir GEDI L4A
file <- 'GEDI04_A_xyz.h5'
H5close()  # Cierra conexiones previas
h5ls(file)  # Lista estructura

# Leer data de un beam
agbd <- h5read(file, '/BEAM0101/geolocation/agbd')
quality <- h5read(file, '/BEAM0101/geolocation/quality_flag')

# Crear tibble
df <- tibble(
  agbd = agbd,
  quality = quality
) %>%
  filter(quality == 1)
```

---

## Validación de Datos Post-Descarga

**Checklist de QA/QC**:

1. **Completitud**: ¿Cuántos datos faltantes (NA/NaN)? Esperado < 5%
2. **Rango**: ¿Valores de biomasa dentro del rango esperado? (50-300 Mg/ha Amazonia)
3. **Distribución**: Histograma de AGBD → ¿multimodal? ¿sesgo?
4. **Outliers**: Boxplot AGBD por mes/región → revisar extremos
5. **Espacialidad**: Mapa de footprints → ¿cobertura uniforme? ¿gaps orbitales?
6. **Correlación GEDI vs ICESat-2** (en overlaps): r > 0.70 esperado

**Script Python de QA/QC**:

```python
import matplotlib.pyplot as plt
import numpy as np

# Cargar datos GEDI filtrados
df = pd.read_csv('gedi_filtered.csv')

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Histograma
axes[0, 0].hist(df['agbd'], bins=50, edgecolor='black')
axes[0, 0].set_xlabel('Biomasa (Mg/ha)')
axes[0, 0].set_title('Distribución AGBD')

# 2. Scatter Biomasa vs Incertidumbre
axes[0, 1].scatter(df['agbd'], df['agbd_std'], alpha=0.5)
axes[0, 1].set_xlabel('Biomasa (Mg/ha)')
axes[0, 1].set_ylabel('Std Dev (Mg/ha)')
axes[0, 1].set_title('Error vs Biomasa')

# 3. Mapa (scatter geográfico)
axes[1, 0].scatter(df['lon'], df['lat'], c=df['agbd'], cmap='viridis', s=2)
axes[1, 0].set_xlabel('Longitude')
axes[1, 0].set_ylabel('Latitude')
axes[1, 0].set_title('Distribución espacial AGBD')

# 4. Boxplot por mes (si hay temporal)
if 'month' in df.columns:
    df.boxplot(column='agbd', by='month', ax=axes[1, 1])
    axes[1, 1].set_xlabel('Month')
    axes[1, 1].set_ylabel('Biomasa (Mg/ha)')

plt.tight_layout()
plt.savefig('gedi_qaqc.png', dpi=150)
plt.show()

# Reportar estadísticas
print(f"N footprints: {len(df)}")
print(f"Biomasa media: {df['agbd'].mean():.1f} Mg/ha")
print(f"Biomasa std: {df['agbd'].std():.1f} Mg/ha")
print(f"Rango: {df['agbd'].min():.1f} - {df['agbd'].max():.1f}")
print(f"Missing values: {df.isnull().sum().sum()}")
```

