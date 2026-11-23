# Plataforma de Asignación y Reportes en Salas · PMV

Prototipo del proyecto del Taller de Proyectos Tecnológicos (María Jesús Escudero · Pablo Rivera · Felipe Vargas · Pablo Velásquez).
Implementa el **LLD** del taller: motor de asignación de salas (CP-SAT) para Ingeniería Eléctrica y Geología + módulo de reportes por QR.

| Bloque | Qué es | Dónde está |
|---|---|---|
| **B1** Datos | Modelo de datos, carga y validación de planillas Excel/CSV | `app/models.py`, `app/validacion.py`, `app/routers/datos.py` |
| **B2** Motor | Formulación CP-SAT (aforo + tiempos de traslado), proceso aparte, máx. 60 s | `app/engine/` |
| **B3** Backend y web | API REST (FastAPI), panel de administración | `app/routers/corridas.py`, `app/templates/panel.html` |
| **B4** QR y soporte | QR por sala, formulario móvil, mesa de incidencias, correo | `app/routers/tickets.py`, `app/services/qr.py`, `scripts/generar_qr.py` |

## Probarlo en 2 minutos (sin Docker)

```bash
make instalar          # crea .venv e instala dependencias (Python 3.12 o 3.13)
make test              # 42 pruebas automáticas
make correr            # http://localhost:8000  (usuario: admin / cambiar-esto)
```

1. Entra a **/panel** → sube `data/ejemplo/salas.xlsx`, luego `traslados.xlsx` y por último `secciones.xlsx` (datos **ficticios**).
2. Pulsa **Ejecutar asignación** → ves malla, indicadores y la comparación contra «primera sala donde cabe». **Exportar Excel** descarga la malla.
3. Sube una planilla con un error (capacidad negativa, horario mal escrito…) y verás el mensaje con **fila y columna**.
4. Abre **/r/E-101** en el celular (o `GET /api/salas/E-101/qr.png` para ver el QR) → envía un reporte → aparece en **/incidencias** (usuario `soporte`).

> **Versión de Python:** usa **3.12 o 3.13**. Con 3.14 o superior `pip` falla con «No matching distribution found for ortools», porque OR-Tools aún no publica paquetes para esas versiones. Si tu sistema trae otra, instala `uv` y usa `uv venv --python 3.13 .venv`.
>
> **Windows** (no tiene `make`):
> ```powershell
> python -m venv .venv
> .venv\Scripts\pip install -r requirements-dev.txt
> .venv\Scripts\python -m pytest
> .venv\Scripts\uvicorn app.main:app --reload
> ```

Con Docker (API + PostgreSQL): `cp .env.example .env`, cambia las contraseñas y `docker compose up --build`.

## Formato de las planillas

- `salas.xlsx`: `codigo_sala · edificio · piso · capacidad · tipo` (`catedra`/`laboratorio`).
- `traslados.xlsx`: `edificio_a · edificio_b · minutos` — minutos caminando entre dos edificios (basta una fila por par, vale en ambos sentidos). Se mide a mano, caminando a paso normal en horario de clases. Dentro de un mismo edificio el traslado es 0 y no se declara. Solo se usa con λ > 0.
- `secciones.xlsx`: `curso · seccion · inscritos · nivel · tipo_sala · horario` · *opcional:* `departamento`. Horario: `LU 10:15-11:45; MI 10:15-11:45` (LU MA MI JU VI SA).

Orden de carga: salas → traslados → secciones.

## Cómo decide el motor

Variable `x[c,s]`; restricciones duras: una sala por sección, capacidad y tipo, sin choques sala-bloque.
Objetivo: `Σ asientos vacíos + λ · minutos de traslado entre clases consecutivas del mismo nivel`.
Tiempo entre dos salas = minutos entre sus edificios (`traslados.xlsx`) + 0,5 min por piso de diferencia. Si falta un par de edificios se asumen 5 min y la corrida lo avisa (constantes en `app/engine/traslado.py`).
**λ = 0** → plan Básico (solo aforo). **λ > 0** → plan Pro. λ es cuántos asientos vacíos se acepta «pagar» por ahorrar 1 minuto de traslado. Con los datos de ejemplo, λ = 1 baja el traslado promedio de ~6 a ~1 min y sube los asientos vacíos ~3 %; con λ ≥ 2 sube ~5 %. Hay que recalibrarlo con datos reales.

## Pruebas de aceptación (ATP) ↔ código

| Criterio | Prueba | Dónde |
|---|---|---|
| CA-01, CA-02 | PA-01 capacidad y choques | `tests/test_motor.py::test_pa01_*` |
| CA-03 | PA-02 aforo vs manual | `test_pa02_*` (vs «primera sala») · **real:** `python -m scripts.comparar_manual salas.xlsx secciones.xlsx traslados.xlsx manual.xlsx` |
| CA-04 | PA-03 tiempo de traslado | `test_pa03_*` |
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
- Se agregó la columna opcional `departamento` (secciones), y se reemplazaron las distancias en metros por **tiempos de traslado en minutos** (`traslados.xlsx`). El criterio CA-04 del ATP se redactó con «distancia»; hay que acordar con el usuario que ahora se mide en minutos.
- Acceso con HTTP Basic y usuarios por variables de entorno (2 roles). Para producción conviene usuarios en base de datos.
- Sin migraciones (se usa `create_all`). Si cambia el modelo en una BD con datos, hay que migrar a mano o adoptar Alembic.
- **No probado:** `docker build`/`docker compose` (no había Docker en el entorno donde se escribió), PostgreSQL real (las pruebas usan SQLite), envío SMTP real y lectura con celulares reales.
