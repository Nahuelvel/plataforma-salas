# Plataforma de Asignación y Reportes en Salas · PMV

Prototipo del proyecto del Taller de Proyectos Tecnológicos (María Jesús Escudero · Pablo Rivera · Felipe Vargas · Pablo Velásquez).
Implementa el **LLD** del taller: motor de asignación de salas (CP-SAT) para Ingeniería Eléctrica y Geología + módulo de reportes por QR.

| Bloque | Qué es | Dónde está |
|---|---|---|
| **B1** Datos | Modelo de datos, carga y validación de planillas Excel/CSV | `app/models.py`, `app/validacion.py`, `app/routers/datos.py` |
| **B2** Motor | Formulación CP-SAT (aforo + distancias), proceso aparte, máx. 60 s | `app/engine/` |
| **B3** Backend y web | API REST (FastAPI), panel de administración | `app/routers/corridas.py`, `app/templates/panel.html` |
| **B4** QR y soporte | QR por sala, formulario móvil, mesa de incidencias, correo | `app/routers/tickets.py`, `app/services/qr.py`, `scripts/generar_qr.py` |

## Probarlo en 2 minutos (sin Docker)

```bash
make instalar          # crea .venv e instala dependencias (Python 3.12+)
make test              # 33 pruebas automáticas
make correr            # http://localhost:8000  (usuario: admin / cambiar-esto)
```

1. Entra a **/panel** → sube `data/ejemplo/salas.xlsx` y luego `data/ejemplo/secciones.xlsx` (datos **ficticios**).
2. Pulsa **Ejecutar asignación** → ves malla, indicadores y la comparación contra «primera sala donde cabe». **Exportar Excel** descarga la malla.
3. Sube una planilla con un error (capacidad negativa, horario mal escrito…) y verás el mensaje con **fila y columna**.
4. Abre **/r/E-101** en el celular (o `GET /api/salas/E-101/qr.png` para ver el QR) → envía un reporte → aparece en **/incidencias** (usuario `soporte`).

Con Docker (API + PostgreSQL): `cp .env.example .env`, cambia las contraseñas y `docker compose up --build`.

## Formato de las planillas

- `salas.xlsx`: `codigo_sala · edificio · piso · capacidad · tipo` (`catedra`/`laboratorio`) · *opcionales:* `edificio_x · edificio_y` (metros, para las distancias).
- `secciones.xlsx`: `curso · seccion · inscritos · nivel · tipo_sala · horario` · *opcional:* `departamento`. Horario: `LU 10:15-11:45; MI 10:15-11:45` (LU MA MI JU VI SA).

## Cómo decide el motor

Variable `x[c,s]`; restricciones duras: una sala por sección, capacidad y tipo, sin choques sala-bloque.
Objetivo: `Σ asientos vacíos + λ · distancia entre clases consecutivas del mismo nivel`.
**λ = 0** → plan Básico (solo aforo). **λ > 0** → plan Pro. Como 1 asiento vacío pesa 1 y la distancia se mide en metros, valores útiles de λ son pequeños (≈ 0.01–0.1); con los datos de ejemplo, λ = 0.03 baja la distancia ~85 % y sube los asientos vacíos ~3 %. Hay que recalibrarlo con datos reales.

## Pruebas de aceptación (ATP) ↔ código

| Criterio | Prueba | Dónde |
|---|---|---|
| CA-01, CA-02 | PA-01 capacidad y choques | `tests/test_motor.py::test_pa01_*` |
| CA-03 | PA-02 aforo vs manual | `test_pa02_*` (vs «primera sala») · **real:** `python -m scripts.comparar_manual salas.xlsx secciones.xlsx manual.xlsx` |
| CA-04 | PA-03 distancias | `test_pa03_*` |
| CA-05 | PA-04 tiempo ≤ 60 s | `test_pa04_*` |
| CA-06 | PA-05 validación 10/10 | `tests/test_validacion.py` |
| CA-08 | PA-06 exportación Excel | `tests/test_api.py::test_flujo_completo` (la lectura por un usuario es manual) |
| CA-07 | PA-07 QR de punta a punta | `tests/test_tickets.py` (las 20 lecturas con celulares reales son manuales) |
| CA-08 | PA-08 SUS | manual |

Planilla de registro: `docs/planilla_registro_atp.csv`. Detalle: `docs/ATP.md`.

## Cómo trabajamos en equipo

Lee **CONTRIBUTING.md** (ramas, PR, revisión). Resumen: nadie sube directo a `main`; una rama por tarea (`feat/B2-...`), PR con CI en verde y 1 aprobación. El backlog vive en GitHub Issues (ver `docs/BACKLOG.md`).

## Diferencias respecto del LLD (decisiones del PMV)

- Los bloques horarios van como JSON dentro de `Seccion` (no hay tabla `Bloque`); `Asignacion` guarda copia de curso/sala/capacidad para que una corrida antigua siga legible.
- Se resuelven **juntos** todos los departamentos seleccionados (el LLD dice «por departamento», pero comparten salas y resolver por separado generaría choques entre ellos).
- Se agregaron columnas opcionales `departamento` (secciones) y `edificio_x/y` (salas) a las planillas.
- Acceso con HTTP Basic y usuarios por variables de entorno (2 roles). Para producción conviene usuarios en base de datos.
- Sin migraciones (se usa `create_all`). Si cambia el modelo en una BD con datos, hay que migrar a mano o adoptar Alembic.
- **No probado:** `docker build`/`docker compose` (no había Docker en el entorno donde se escribió), PostgreSQL real (las pruebas usan SQLite), envío SMTP real y lectura con celulares reales.
