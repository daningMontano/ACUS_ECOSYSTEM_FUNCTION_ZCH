# Referencia: validación de modelos espaciales

## Principio central

En modelos espaciales, una partición aleatoria entrenamiento/prueba puede sobreestimar el desempeño debido a autocorrelación espacial. Cuando los puntos cercanos son similares, el modelo puede parecer preciso aunque no generalice a nuevas zonas.

## Validación mínima

Para clasificación de coberturas o predicción espacial se debe reportar:

- Matriz de confusión.
- Accuracy.
- Precision.
- Recall.
- F1-score.
- Kappa.
- Balance de clases.
- Número de muestras por clase.
- Estrategia de partición.
- Resolución espacial del producto.
- Limitaciones de escala y muestreo.

## Validación espacial por bloques

Usar cuando:

- Las muestras están agrupadas.
- Existe autocorrelación espacial.
- El objetivo es transferir el modelo a nuevas zonas.
- Se trabaja con biodiversidad, deforestación, biomasa, agricultura o riesgo ambiental.

Procedimiento general:

1. Crear bloques espaciales.
2. Asignar cada muestra a un bloque.
3. Separar bloques completos para entrenamiento y prueba.
4. Entrenar sin mezclar puntos cercanos entre train/test.
5. Evaluar métricas por fold espacial.

## Validación temporal

Usar cuando:

- El modelo se aplica a años futuros.
- Se entrenó con un periodo y se predice otro.
- Se evalúan cambios, sequías, incendios o deforestación.

Procedimiento general:

1. Entrenar con años anteriores.
2. Validar con años posteriores.
3. Evaluar estabilidad temporal.
4. Revisar si hay cambio de distribución entre periodos.

## Métricas

### Accuracy
Proporción total de aciertos. Puede ser engañosa con clases desbalanceadas.

### Precision
De las predicciones positivas, cuántas fueron correctas. Útil cuando los falsos positivos son costosos.

### Recall
De los positivos reales, cuántos fueron detectados. Útil cuando los falsos negativos son críticos, por ejemplo deforestación, incendios o presencia de especies.

### F1-score
Media armónica entre precision y recall. Útil con clases desbalanceadas.

### Kappa
Mide acuerdo corregido por azar. Puede ser útil en clasificación de coberturas, pero no debe ser la única métrica.

### ROC AUC
Evalúa discriminación en modelos probabilísticos binarios. Puede ser inestable con muestras pequeñas o fuerte desbalance.

## Revisión espacial de errores

Además de métricas, revisar:

- Mapas de error.
- Concentración espacial de falsos positivos.
- Concentración espacial de falsos negativos.
- Errores por clase.
- Errores en bordes de cobertura.
- Errores asociados a nubes, sombras, pendiente o humedad.

## Incertidumbre

Cuando sea posible, reportar:

- Probabilidad de clase.
- Margen entre clase ganadora y segunda clase.
- Desviación entre árboles en Random Forest.
- Intervalos por bootstrap.
- Mapas de incertidumbre.
