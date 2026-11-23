# Arquitectura (resumen)

```
Administración / Soporte (navegador) ──HTTPS──▶ FastAPI (B3) ──SQL──▶ PostgreSQL (B1)
Estudiante / profesor (celular + QR) ──HTTPS──▶   │  valida con Pydantic
                                                  ├──proceso aparte (JSON por stdin/stdout, máx. 60 s)──▶ Motor CP-SAT (B2)
                                                  └──SMTP──▶ correo a soporte (B4)
```

- **El motor** (`app/engine/`) no importa FastAPI ni SQLAlchemy: recibe listas de dicts y devuelve un dict. Se puede probar y usar solo. La API lo lanza con `python -m app.engine.runner`, así un cálculo largo no tumba el servidor.
- **Corridas asíncronas:** `POST /api/corridas` responde 202 y calcula en segundo plano; el panel consulta `GET /api/corridas/{id}` hasta que el estado deja de ser `en_curso`.
- **Estados de una corrida:** `en_curso → optima | factible | infactible | error`. «factible» = se acabó el tiempo y se entrega la mejor solución encontrada.
- **Reproducibilidad:** cada corrida guarda sus parámetros (departamentos, λ, salas fijas, límite de tiempo).
- **Decisión humana:** la plataforma sugiere; para fijar una sala y recalcular se envía `fijas: {"CURSO-SEC": "COD_SALA"}` en `POST /api/corridas` (la pantalla para hacerlo desde el panel está en el backlog).
- **Prioridad de tickets:** `alta` si la sala tiene clase ahora según la última corrida óptima/factible.

## API
| Método | Ruta | Acceso | Qué hace |
|---|---|---|---|
| POST | `/api/datos/salas` | admin | Carga y valida salas (upsert por código) |
| POST | `/api/datos/traslados` | admin | Carga y valida minutos entre edificios (reemplaza la tabla; requiere salas) |
| POST | `/api/datos/secciones?semestre=` | admin | Carga y valida secciones (reemplaza ese semestre) |
| POST | `/api/corridas` | admin | Lanza una optimización |
| GET | `/api/corridas/{id}` | admin | Estado, indicadores y malla |
| GET | `/api/corridas/{id}/excel` | admin | Descarga la malla |
| POST | `/api/tickets` | público | Crea un ticket (desde el QR) |
| GET · PATCH | `/api/tickets` | soporte/admin | Lista y actualiza tickets |
| GET | `/api/salas/{codigo}/qr.png` | admin | QR de la sala |

Documentación interactiva en `/docs`.
