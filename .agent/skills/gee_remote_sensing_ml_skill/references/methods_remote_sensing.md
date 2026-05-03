# Referencia: métodos de sensores remotos

## Índices espectrales

### NDVI
Uso: vigor vegetal, cobertura verde, productividad relativa.

Limitaciones:
- Saturación en bosques densos.
- Sensible a suelo expuesto y atmósfera.

### EVI
Uso: vegetación densa, bosques tropicales, reducción parcial de saturación del NDVI.

Limitaciones:
- Requiere banda azul.
- Puede ser sensible a ruido atmosférico.

### NDWI / MNDWI / AWEI
Uso: cuerpos de agua, inundaciones, humedad superficial.

Consideraciones:
- MNDWI suele mejorar separación agua-suelo urbano.
- AWEI puede ser útil para sombras y superficies oscuras.

### NBR
Uso: severidad de incendios, pérdida de vegetación, degradación.

## Detección de cambios

### CCDC
Adecuado para series temporales densas y detección de cambios continuos.
Útil para deforestación, degradación, cambio de cobertura y monitoreo multianual.

### LandTrendr
Adecuado para trayectorias de cambio, disturbios y recuperación de vegetación.

### BFAST
Adecuado para descomponer series temporales en tendencia, estacionalidad y rupturas.

### BULC
Adecuado para clasificaciones dinámicas y actualización temporal de cobertura.

## Clasificación supervisada

### Random Forest
Modelo robusto para clasificación de coberturas.
Funciona bien con predictores espectrales, radar, topográficos e índices derivados.

Riesgos:
- Sobreajuste si las muestras están espacialmente autocorrelacionadas.
- Importancia de variables puede estar sesgada por correlación entre predictores.

### SVM
Útil con pocas muestras y separaciones complejas.

Riesgos:
- Sensible a escalamiento de variables.
- Requiere ajuste de kernel, costo y gamma.

### CNN
Útil para clasificación basada en textura, objetos o imágenes parcheadas.

Riesgos:
- Requiere más datos.
- Mayor costo computacional.
- Debe validarse espacialmente.

## Clasificación no supervisada

### K-means
Útil para exploración inicial de coberturas o estratificación ambiental.

Limitaciones:
- No interpreta clases ecológicas por sí solo.
- Requiere asignación posterior de significado.

### Spectral Clustering
Útil cuando las clases no son esféricas en el espacio de variables.

Limitaciones:
- Más costoso computacionalmente.
- Menos directo de implementar a gran escala.
