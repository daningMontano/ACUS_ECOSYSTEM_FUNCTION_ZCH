# GEE Remote Sensing & Spatial ML Skill

Skill general para un chatbot asesor técnico en Google Earth Engine, sensores remotos y machine learning geoespacial.

## Estructura

```text
gee_remote_sensing_ml_skill/
├── SKILL.md
├── README.md
├── references/
│   ├── datasets_and_sensors.md
│   ├── methods_remote_sensing.md
│   ├── spatial_ml_validation.md
│   └── deployment_and_reproducibility.md
├── templates/
│   ├── analysis_plan_template.md
│   └── spatial_model_validation_checklist.md
└── scripts/
    ├── gee_javascript/
    │   └── gee_indices_and_export_template.js
    ├── python/
    │   └── geemap_workflow_template.py
    └── r/
        └── rgee_workflow_template.R
```

## Uso recomendado

1. Copiar toda esta carpeta dentro del directorio de skills del sistema o chatbot.
2. Usar `SKILL.md` como instrucción principal.
3. Mantener los archivos de `references/` como conocimiento técnico de apoyo.
4. Usar `templates/` para estructurar respuestas.
5. Usar `scripts/` como código base editable para JavaScript/GEE, Python/geemap y R/rgee.

## Principio operativo

El chatbot no debe saltar directamente al código. Primero debe construir un plan metodológico mínimo y luego generar código reproducible en el lenguaje solicitado.
