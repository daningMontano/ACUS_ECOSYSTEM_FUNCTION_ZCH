# Protocolos Especiales: Ecosistemas Tropicales Saturados (Amazonía)

## Tabla de Contenidos
- [Diagnóstico de Saturación](#diagnóstico-de-saturación)
- [Mitigaciones Técnicas](#mitigaciones-técnicas)
- [Métricas Avanzadas de Estructura](#métricas-avanzadas-de-estructura)
- [Rangos Esperados por Bioma Amazónico](#rangos-esperados-por-bioma-amazónico)
- [Casos de Estudio](#casos-de-estudio)

---

## Diagnóstico de Saturación

### ¿Qué es la saturación?

En **bosques muy densos** (biomasa > 250 Mg/ha), el pulso Lidar GEDI puede no penetrar completamente 
hasta el suelo. Consecuencias:

1. **Altura subestimada**: RH100 (máximo detectado) < altura real del dosel
2. **Waveform truncado**: Forma de onda cortada, sin cola en suelo
3. **Error en biomasa**: Modelo alométrico EBT usa RH → subestima AGB

### Indicadores de Saturación

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos GEDI filtrados
gedi = pd.read_csv('gedi_filtered.csv')

# Indicador 1: RH98 ~ RH100 (muy cercanos)
gedi['rh_tail'] = gedi['rh100'] - gedi['rh98']
saturated_tail = (gedi['rh_tail'] < 2).sum() / len(gedi) * 100

print(f"Footprints con RH98≈RH100 (posible saturación): {saturated_tail:.1f}%")

# Indicador 2: RH amplitude bajo (rango total pequeño)
gedi['rh_amplitude'] = gedi['rh100'] - gedi['rh0']
low_amplitude = (gedi['rh_amplitude'] < 15).sum() / len(gedi) * 100

print(f"Footprints con amplitud RH < 15m: {low_amplitude:.1f}%")

# Indicador 3: Distribución espacial de RH100
plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.hist(gedi['rh100'], bins=50, edgecolor='black')
plt.xlabel('RH100 (m)')
plt.title('Distribución RH100')
if gedi['rh100'].mean() > 30:  # Sugiere saturación en bosques altos
    plt.axvline(x=gedi['rh100'].mean(), color='r', linestyle='--', 
                label=f'Mean: {gedi["rh100"].mean():.1f}m')
plt.legend()

plt.subplot(1, 3, 2)
plt.scatter(gedi['rh100'], gedi['rh_tail'], alpha=0.3, s=5)
plt.axhline(y=2, color='r', linestyle='--', label='Threshold (2m)')
plt.xlabel('RH100 (m)')
plt.ylabel('RH100 - RH98 (m)')
plt.title('Detección Saturación')
plt.legend()

plt.subplot(1, 3, 3)
plt.hist(gedi['agbd_std'] / gedi['agbd'], bins=50, edgecolor='black')
plt.xlabel('Relative Error (Std/AGB)')
plt.axvline(x=0.5, color='r', linestyle='--', label='50% threshold')
plt.title('Error Relativo AGBD')
plt.legend()

plt.tight_layout()
plt.savefig('saturation_diagnosis.png', dpi=150)
plt.show()
```

### Visualización de Waveforms L1B

Para diagnóstico visual riguroso, inspeccionar waveforms L1B:

```python
import h5py
import numpy as np

# Abrir archivo GEDI L1B
with h5py.File('GEDI01_B_yyyy_doy_hh_mm_ss_vvv_xyz_rev001.h5', 'r') as f:
    
    beam = 'BEAM0110'  # Haz específico
    
    # Leer waveform (500 samples)
    waveform = f[beam]['waveform']['rx_waveform'][:]  # (n_footprints, 500)
    
    # Plotear ejemplos
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    for idx, ax in enumerate(axes.flat):
        wf = waveform[idx, :]
        ax.plot(range(len(wf)), wf, linewidth=1)
        ax.set_xlabel('Sample index')
        ax.set_ylabel('Amplitude (DN)')
        ax.set_title(f'Waveform {idx}')
        
        # Indicador visual de saturación: tail plano (no decae)
        if wf[-50:].mean() > wf[-100:-50].mean() * 0.8:
            ax.text(0.5, 0.95, 'POSIBLE SATURACIÓN', 
                   transform=ax.transAxes, color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('waveforms_visual.png', dpi=150)
```

### Comparación GEDI vs Validación de Campo

```python
# Si disponibles datos de campo (altura o biomasa medida)
field = pd.read_csv('field_validation.csv')  # cols: lon, lat, h_measured_m, agb_measured_mgh

# Unir con GEDI (buffer 50m)
from scipy.spatial.distance import cdist

gedi_coords = gedi[['lon', 'lat']].values
field_coords = field[['lon', 'lat']].values

distances = cdist(gedi_coords, field_coords, 'euclidean')
closest_gedi_idx = distances.argmin(axis=0)

merged = pd.DataFrame({
    'rh100': gedi.iloc[closest_gedi_idx]['rh100'].values,
    'agbd': gedi.iloc[closest_gedi_idx]['agbd'].values,
    'h_measured': field['h_measured_m'].values,
    'agb_measured': field['agb_measured_mgh'].values,
})

# Comparación
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# RH100 vs altura de campo
axes[0].scatter(merged['h_measured'], merged['rh100'], alpha=0.6)
axes[0].plot([0, merged['h_measured'].max()], [0, merged['h_measured'].max()], 'r--', lw=2)
axes[0].set_xlabel('Altura de Campo (m)')
axes[0].set_ylabel('RH100 GEDI (m)')
axes[0].set_title(f'RH100 vs Altura (R²={np.corrcoef(merged["h_measured"], merged["rh100"])[0,1]**2:.3f})')

# AGBD vs biomasa campo
axes[1].scatter(merged['agb_measured'], merged['agbd'], alpha=0.6)
axes[1].plot([0, merged['agb_measured'].max()], [0, merged['agb_measured'].max()], 'r--', lw=2)
axes[1].set_xlabel('Biomasa Campo (Mg/ha)')
axes[1].set_ylabel('AGBD GEDI (Mg/ha)')
r2_agb = np.corrcoef(merged['agb_measured'], merged['agbd'])[0,1]**2
rmse_agb = np.sqrt(np.mean((merged['agbd'] - merged['agb_measured'])**2))
axes[1].set_title(f'AGBD vs Biomasa (R²={r2_agb:.3f}, RMSE={rmse_agb:.1f})')

# Indicador de saturación: R² bajo en biomasa alta
high_biomass = merged['agb_measured'] > 250
if high_biomass.sum() > 5:
    r2_high = np.corrcoef(merged.loc[high_biomass, 'agb_measured'], 
                         merged.loc[high_biomass, 'agbd'])[0,1]**2
    print(f"R² en biomasa ALTA (>250): {r2_high:.3f} (comparar con {r2_agb:.3f} global)")
    if r2_high < r2_agb - 0.15:
        print("⚠️  Saturación probable: desempeño degradado en biomasa alta")

plt.tight_layout()
plt.savefig('field_validation.png', dpi=150)
plt.show()
```

---

## Mitigaciones Técnicas

### 1. Selección Estricta de Haces

```python
# Opción 1: Usar solo haces de POTENCIA ALTA
gedi_clean = gedi[gedi['beam'].isin(['BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011'])]

# Opción 2: Aumentar sensibilidad (penetración)
gedi_clean = gedi[gedi['sensitivity'] > 0.995]  # vs defecto 0.98

print(f"Footprints tras filtros estrictos: {len(gedi_clean)} ({len(gedi_clean)/len(gedi)*100:.1f}%)")
```

### 2. Usar Modelo Alométrico Regional (vs Global)

```python
# L4A AGB usa modelo global EBT (Evergreen Broadleaf)
# Para Amazonía específica, entrenar modelo regional local

# Opción: No usar L4A directo, recalcular a partir de RH + datos de campo locales

from sklearn.ensemble import RandomForestRegressor

# Training: RH metrics + campo biomasa
X_train = gedi_field[['rh25', 'rh50', 'rh75', 'rh98']].values
y_train = gedi_field['agb_measured'].values

rf_local = RandomForestRegressor(max_depth=8, random_state=42)
rf_local.fit(X_train, y_train)

# Predicción: aplicar a todo GEDI
gedi['agbd_local'] = rf_local.predict(gedi[['rh25', 'rh50', 'rh75', 'rh98']].values)

# Comparación
print(f"GEDI AGBD (EBT global): media={gedi['agbd'].mean():.1f}, std={gedi['agbd'].std():.1f}")
print(f"GEDI AGBD (RF local): media={gedi['agbd_local'].mean():.1f}, std={gedi['agbd_local'].std():.1f}")
```

### 3. Fusión con SAR (Sentinel-1)

SAR backscatter (VV, VH) **NO satura** a biomasa alta como Lidar. Estrategia: combinar.

```python
# Cargar Sentinel-1 (VV, VH) en mismas ubicaciones GEDI
s1_vv = load_s1_band('VV', gedi_coords)  # función auxiliar
s1_vh = load_s1_band('VH', gedi_coords)

gedi['vv_vh_ratio'] = s1_vv / (s1_vh + 1e-6)
gedi['vv_vh_sum'] = s1_vv + s1_vh

# Entrenar modelo combinado (Lidar + SAR)
features_combined = gedi[['rh50', 'rh_amplitude', 'vv_vh_ratio', 'vv_vh_sum']].values
y = gedi_field['agb_measured'].values

rf_fusion = RandomForestRegressor(max_depth=10, random_state=42)
rf_fusion.fit(features_combined, y)

gedi['agbd_fusion'] = rf_fusion.predict(features_combined)

# Evaluación
print("Feature importance (Lidar+SAR fusion):")
for feat, imp in zip(['RH50', 'RH_amplitude', 'VV/VH ratio', 'VV+VH sum'],
                     rf_fusion.feature_importances_):
    print(f"  {feat}: {imp:.3f}")

# SAR frecuentemente contribuye 30-40% en bosques saturados
```

### 4. Detección y Exclusión de Outliers

```python
# Descartar footprints con error de estimación > 50%
gedi_clean = gedi[gedi['agbd_std'] / gedi['agbd'] < 0.50]

# Descartar footprints en pendientes pronunciadas (>15°, error topográfico)
# (requiere SRTM slope en cada ubicación)
gedi_clean = gedi_clean[gedi_clean['slope'] < 15]

# Descartar footprints sin validación de elevación
# |elev_lidar - SRTM| < 20m (típico)
gedi_clean = gedi_clean[np.abs(gedi_clean['elev_lidar'] - gedi_clean['elev_srtm']) < 20]

print(f"Footprints tras limpieza de outliers: {len(gedi_clean)} ({len(gedi_clean)/len(gedi)*100:.1f}%)")
```

---

## Métricas Avanzadas de Estructura

### Índices Basados en RH

```python
# RH cuantiles dan forma del perfil vertical
gedi['rh_range_25_75'] = gedi['rh75'] - gedi['rh25']  # Rango intercuartílico
gedi['rh_uniformity'] = gedi['rh25'] / gedi['rh75']   # 1.0 = uniforme, <0.5 = multiestrato
gedi['rh_ratio_50_100'] = gedi['rh50'] / gedi['rh100']  # Proporción biomasa en mitad inferior

# Interpretar:
# - rh_uniformity ~ 1.0 → estructura simple (plantación, sabana)
# - rh_uniformity ~ 0.3 → multiestrato complejo (bosque primario)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].hist(gedi['rh_uniformity'], bins=50, edgecolor='black')
axes[0].set_xlabel('RH Uniformity')
axes[0].set_title('Índice de Uniformidad Vertical')
axes[0].axvline(x=0.5, color='r', linestyle='--', label='Multiestrato threshold')
axes[0].legend()

axes[1].scatter(gedi['rh_uniformity'], gedi['agbd'], alpha=0.3, s=5)
axes[1].set_xlabel('RH Uniformity')
axes[1].set_ylabel('AGBD (Mg/ha)')
axes[1].set_title('Biomasa vs Estructura')

# Densidad de volumen (PAVD proxy): RH_amplitude / max_height
gedi['pavd_proxy'] = gedi['rh_amplitude'] / (gedi['rh100'] + 0.1)
axes[2].hist(gedi['pavd_proxy'], bins=50, edgecolor='black')
axes[2].set_xlabel('PAVD Proxy')
axes[2].set_title('Densidad de Volumen')

plt.tight_layout()
plt.savefig('structural_metrics.png', dpi=150)
plt.show()
```

### Plant Area Index (PAI) Aproximado

```python
# PAI ≈ función de RH25 (penetración 25% altura)
# RH25 bajo → dosel denso → PAI alto
# RH25 alto → poco dosel en base → PAI bajo

gedi['pai_proxy'] = 1 - (gedi['rh25'] / gedi['rh100'])  # 0-1 scale

# Rango esperado Amazonia:
# - Bosque primario denso: PAI 5-8 (intercepta 80-90% luz)
# - Bosque secundario: PAI 3-5
# - Sabana: PAI 1-3

print(f"PAI proxy media (Amazonia): {gedi['pai_proxy'].mean():.2f} (rango: {gedi['pai_proxy'].min():.2f}-{gedi['pai_proxy'].max():.2f})")
```

---

## Rangos Esperados por Bioma Amazónico

### Tabla de Referencia

```python
# Definir biomas (requiere mapas Amazonia, e.g., INPA, IBAMA)
biomas = {
    'Bosque Denso Primario': {
        'agbd_range': (200, 320),
        'rh100_range': (25, 50),
        'rh_uniformity_range': (0.2, 0.4),
        'pai_proxy_range': (5, 8),
    },
    'Bosque Secundario (>30 años)': {
        'agbd_range': (120, 200),
        'rh100_range': (18, 28),
        'rh_uniformity_range': (0.35, 0.55),
        'pai_proxy_range': (3.5, 5),
    },
    'Bosque Secundario Joven (5-30 años)': {
        'agbd_range': (50, 120),
        'rh100_range': (10, 18),
        'rh_uniformity_range': (0.50, 0.70),
        'pai_proxy_range': (2, 3.5),
    },
    'Cerrado/Sabana': {
        'agbd_range': (20, 60),
        'rh100_range': (5, 12),
        'rh_uniformity_range': (0.65, 0.95),
        'pai_proxy_range': (0.5, 1.5),
    },
}

# Validar: ¿footprints caen en rangos esperados?
bioma = 'Bosque Denso Primario'
agbd_range = biomas[bioma]['agbd_range']
outlier_mask = (gedi['agbd'] < agbd_range[0]) | (gedi['agbd'] > agbd_range[1])

print(f"{bioma}:")
print(f"  Footprints esperados: {(~outlier_mask).sum()}")
print(f"  Outliers (fuera de rango): {outlier_mask.sum()} ({outlier_mask.sum()/len(gedi)*100:.1f}%)")
print(f"  AGBD observada: {gedi['agbd'].min():.1f}-{gedi['agbd'].max():.1f} Mg/ha")
```

---

## Casos de Estudio

### Caso 1: Saturación en Floresta Amazónica (Manaus, Amazonas)

**Descripción**: Bosque primario denso, biomasa > 270 Mg/ha

**Diagnóstico**:
- RH100 media: 38 m (consistente)
- RH98 media: 35.2 m (RH100-RH98 = 2.8 m, bajo → probable saturación)
- Waveforms L1B: tail plano después de 400 samples
- Comparación campo: RH100 GEDI vs altura medida R² = 0.68 (vs 0.85 esperado)

**Solución implementada**:
1. Filtrar sensitivity > 0.995 (quitó 15% datos)
2. Incluir Sentinel-1 SAR (VV/VH) en modelo ML
3. Entrenar RF local con 25 parcelas de campo locales
4. Resultado: RMSE mejoró de 26 Mg/ha (L4A global) a 19 Mg/ha (RF local + SAR)

**Publicación referente**: Avitabile et al. (2016), Silva et al. (2019)

### Caso 2: Deforestación Reciente (Rondônia, Brasil)

**Descripción**: Mosaico bosque intacto + deforestación, biomasa 50-150 Mg/ha

**Características**:
- Bosques jóvenes secundarios (5-15 años): RH100 10-18 m, sin saturación
- Bordes de deforestación: transitorio RH muy variable
- Heterogeneidad alta → texture_contrast (GLCM) importante predictor

**Solución**:
1. NO requiere mitigación de saturación (biomasa no alcanza threshold)
2. NDVI + NDRE (Sentinel-2) son predictores fuertes (R² > 0.75)
3. Validación estratificada: RMSE similar en todos rangos (~10 Mg/ha)

**Implicación**: Modelos simples (RF solo Sentinel) funcionan bien aquí

### Caso 3: Páramo Andino (Colombia)

**Descripción**: Baja biomasa, topografía pronunciada, atmósfera clara

**Características**:
- Biomasa 20-80 Mg/ha (sin saturación)
- Elevaciones 3000-4500 m, slopes > 20° frecuentes
- Nubes persistentes, Sentinel-2 disponibilidad < 40%

**Challenges**:
1. GEDI coverage irregular (órbita inclinada, menos pases en altas latitudes)
2. Topografía: slope > 20° → outliers, requiere SRTM filtering
3. Sentinel-2: pocas imágenes sin nubes → usar series temporales (mediana anual)

**Solución**:
1. ICESat-2 complementa GEDI (cobertura completa)
2. Topographic correction: incluir slope, aspect como predictores
3. Usar Sentinel-1 (penetra nubes)
4. Menor N de training (GEDI sparse) → Random Forest vs XGBoost

---

## Checklist de Validación para Amazonía

Antes de usar modelo para publicación/análisis:

- [ ] ¿Diagnosticada saturación? (RH98-RH100, waveforms L1B)
- [ ] ¿Filtrados haces débiles? (BEAM0011 excluido)
- [ ] ¿Sensibilidad > 0.98?
- [ ] ¿Datos de campo N > 30 sitios en región de estudio?
- [ ] ¿Validación cruzada geográfica (no random split)?
- [ ] ¿RMSE reportado separadamente para biomasa alta (>250 Mg/ha)?
- [ ] ¿Incertidumbre por píxel mapeada (agbd_std)?
- [ ] ¿Comparación modelo local vs EBT global?
- [ ] ¿SAR (Sentinel-1) incluido si biomasa > 200 Mg/ha?
- [ ] ¿Limitaciones de saturación reconocidas en paper/reporte?

