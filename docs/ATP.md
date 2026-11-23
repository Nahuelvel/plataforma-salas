# Proceso de aceptación (ATP)

Fuente: PDF «Diseño de Detalle (LLD) y Proceso de Aceptación (ATP)» del taller. Resumen operativo para el equipo.

| ID | Criterio | Umbral | Prueba | Automática | Manual |
|---|---|---|---|---|---|
| CA-01 | Respeta la capacidad | 0 violaciones | PA-01 | `test_pa01` | — |
| CA-02 | Sin choques | 0 choques | PA-01 | `test_pa01` | — |
| CA-03 | Mejora el aforo útil | ≥ 15 % menos asientos vacíos vs manual | PA-02 | vs «primera sala» | `scripts.comparar_manual` con la asignación real |
| CA-04 | Reduce traslados | ≥ 10 % menos **tiempo de traslado** (minutos; en el LLD decía «distancia»), asientos vacíos ≤ +5 % | PA-03 | `test_pa03` | idem con datos reales |
| CA-05 | Responde rápido | ≤ 60 s en 5/5 corridas | PA-04 | `test_pa04` | repetir en la VM de 2 vCPU / 4 GB |
| CA-06 | Valida los datos | 10/10 planillas rechazadas con fila y columna | PA-05 | `tests/test_validacion.py` | probar con planillas reales de la secretaría |
| CA-07 | Reporte QR funciona | ≥ 19/20 lecturas; ticket en ≤ 10 s | PA-07 | flujo API | 20 lecturas con Android + iOS, wifi y datos |
| CA-08 | Fácil de usar | SUS ≥ 70; 4/5 usuarios en ≤ 10 min | PA-06, PA-08 | exportación Excel | usuarios reales |

**Regla de aceptación:** se cumplen todos los *Must have* (CA-01, 02, 05, 06) y al menos 3 de los otros 4.

## Pasos
1. Criterios acordados con el usuario (secretaría docente).
2. Casos de prueba (PA-01…PA-08, formato «Prueba X» en el anexo del PDF).
3. Ejecución: correr cada prueba y registrar en `planilla_registro_atp.csv` (pasó / falló, commit probado).
4. Resolución: cada falla abre un issue (plantilla «Falla en prueba de aceptación»), se corrige y se repite la prueba.
5. Evaluación: matriz criterio × resultado.
6. Aprobación: acta firmada por el equipo y el usuario, con fecha, versión probada y resultados.

## Pendiente que depende de la secretaría
La asignación manual real del semestre (para PA-02 y PA-03). Si no se consigue, PA-02 se hace contra «primera sala donde cabe» (ya está en cada corrida).
