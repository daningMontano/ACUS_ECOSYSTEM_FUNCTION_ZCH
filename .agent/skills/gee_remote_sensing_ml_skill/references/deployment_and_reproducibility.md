# Referencia: despliegue, exportación y reproducibilidad

## Exportación en Google Earth Engine

### GeoTIFF a Google Drive
Usar para mapas raster finales, índices, probabilidades, clasificaciones y variables ambientales.

### CSV a Google Drive
Usar para tablas de muestras, métricas, extracción por puntos o regiones.

### Cloud Assets
Usar cuando el producto será reutilizado dentro de GEE o compartido con otros usuarios.

## Earth Engine Apps

Usar cuando el objetivo sea publicar una interfaz interactiva sin construir una aplicación externa.

Componentes comunes:

- Mapa.
- Panel lateral.
- Selector de fechas.
- Selector de capas.
- Leyenda.
- Botones de exportación o consulta.
- Gráficos temporales.

## Reproducibilidad

Un proyecto reproducible debe incluir:

- Script principal.
- Parámetros editables.
- Descripción del área de estudio.
- Versiones de datasets.
- Fecha de descarga o procesamiento.
- Carpeta de resultados.
- Métricas de validación.
- Metadatos del modelo.
- Limitaciones conocidas.

## Sphinx

Usar para documentación técnica de paquetes, funciones y pipelines en Python.

## Jupytext

Usar para sincronizar notebooks con scripts `.py`, permitiendo control de versiones con Git.
