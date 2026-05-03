# Checklist de validación de modelos espaciales

## Datos

- [ ] Las muestras tienen coordenadas válidas.
- [ ] Las clases están correctamente etiquetadas.
- [ ] Se revisó el número de muestras por clase.
- [ ] Se identificó desbalance de clases.
- [ ] Se revisaron duplicados espaciales.
- [ ] Se revisó sesgo de muestreo.

## Partición

- [ ] Se evitó depender solo de partición aleatoria.
- [ ] Se evaluó autocorrelación espacial.
- [ ] Se consideró validación por bloques espaciales.
- [ ] Se consideró validación temporal si hay varios años.
- [ ] No hay fuga de datos entre entrenamiento y prueba.

## Métricas

- [ ] Matriz de confusión.
- [ ] Accuracy.
- [ ] Precision.
- [ ] Recall.
- [ ] F1-score.
- [ ] Kappa.
- [ ] ROC AUC si el modelo es binario probabilístico.
- [ ] Métricas por clase.

## Evaluación espacial

- [ ] Mapa de predicción.
- [ ] Mapa de probabilidad o incertidumbre.
- [ ] Mapa de errores.
- [ ] Revisión de falsos positivos.
- [ ] Revisión de falsos negativos.
- [ ] Evaluación por zonas ecológicas o territoriales.

## Reporte

- [ ] Se reportó sensor usado.
- [ ] Se reportó periodo de análisis.
- [ ] Se reportó resolución espacial.
- [ ] Se reportó número de muestras.
- [ ] Se reportó método de validación.
- [ ] Se reportaron limitaciones.
