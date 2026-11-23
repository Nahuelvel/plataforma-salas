# Backlog del PMV

Generado desde `docs/backlog.tsv`, que usa `scripts/setup_github.sh` para crear los issues en GitHub. **Una vez creados, el tablero de GitHub es la fuente de verdad.**

Prioridad según el LLD: *must* = CA-01, 02, 05, 06 y salida legible; *should* = traslados (plan Pro) y usabilidad; *could* = módulo QR.

## 1 · PMV (motor y panel)

- **[B3] Panel: fijar una sala y recalcular** `should,B3`  
  Flujo «¿No convence?» del LLD: desde la malla, elegir una sección, fijar su sala y relanzar. La API ya acepta fijas en POST /api/corridas; falta la pantalla.
- **[B3] Panel: comparar con la corrida anterior** `should,B3`  
  El LLD pide indicadores comparados con la asignación anterior. Hoy se compara con «primera sala donde cabe».
- **[B3] Panel: subir la asignación manual para el A/B (PA-02)** `could,B3`  
  Hoy se hace con scripts/comparar_manual.py. Agregar endpoint y botón en el panel.

## 2 · Datos y ATP

- **[B1] Conseguir datos reales de Eléctrica y Geología (salas, secciones, asignación manual)** `must,B1,datos`  
  Pedir a la secretaría docente las planillas del semestre y la asignación manual real (pregunta abierta del LLD). Guardarlas fuera del repo. Sin la asignación manual, PA-02 usa «primera sala donde cabe». Criterio: CA-03, CA-04.
- **[B1] Medir los tiempos de traslado reales entre edificios** `should,B1,datos`  
  Caminar entre cada par de edificios a paso normal en horario de clases y completar traslados.xlsx (edificio_a, edificio_b, minutos). Sin esto λ asume 5 min. Criterio: CA-04.
- **[B2] Calibrar λ con datos reales** `should,B2`  
  Con datos reales, barrer λ (≈ 0.5–3 asientos por minuto) y elegir el que cumpla CA-04 (≥10 % menos tiempo de traslado, asientos vacíos ≤ +5 %). Documentar el valor en el README. Usar scripts/comparar_manual.py.
- **[ATP] Acordar con la secretaría que CA-04 se mida en minutos de traslado** `must,atp`  
  El criterio se acordó como «≥ 10 % menos distancia». Pasamos a tiempo de traslado: dejar la nueva redacción confirmada con el usuario y los profesores antes de ejecutar PA-03.

## 3 · Aceptación (ATP)

- **[B2] Probar rendimiento en la VM de 2 vCPU / 4 GB** `must,B2,atp`  
  Ejecutar PA-04 (5 corridas ≤ 60 s) en la máquina del LLD y una prueba 3 veces más grande (informativa). Ajustar SOLVER_HILOS si hace falta. Criterio: CA-05.
- **[B4] Desplegar en VM con HTTPS** `must,B4,infra`  
  Ubuntu 24.04, Docker Compose, dominio y certificado (p. ej. Caddy o nginx + Let's Encrypt). Configurar BASE_URL (va impreso en los QR), contraseñas y SMTP.
- **[B4] Imprimir e instalar placas QR piloto (3 salas)** `could,B4`  
  python -m scripts.generar_qr salas.xlsx qr_salida --base-url https://DOMINIO. Vinilo laminado 10×10 cm junto a la puerta.
- **[ATP] Ejecutar PA-01 a PA-06 y registrar resultados** `must,atp`  
  Con datos reales. Registrar en docs/planilla_registro_atp.csv con el commit probado. Cada falla abre un issue con la plantilla ATP.
- **[ATP] Ejecutar PA-07 (20 lecturas QR con Android e iOS)** `could,atp`  
  Combinar salas, teléfonos y redes (wifi/datos). Cronometrar hasta que el ticket aparece en la mesa (≤ 10 s). Probar la URL corta de respaldo. Criterio: CA-07.
- **[ATP] Ejecutar PA-08 (SUS con 5 usuarios)** `should,atp`  
  Encuesta SUS ≥ 70 y tarea completa ≤ 10 min en 4 de 5 usuarios. Criterio: CA-08.
- **[ATP] Matriz criterio × resultado y acta de aceptación** `must,atp`  
  Aceptar si se cumplen CA-01, 02, 05 y 06 y al menos 3 de los otros 4. Acta firmada por el equipo y la secretaría docente / profesor guía.

## 4 · Producción

- **[B3] Usuarios en base de datos en vez de variables de entorno** `could,B3`  
  Hoy hay 2 usuarios por .env con HTTP Basic. Para producción: tabla Usuario (correo, rol), hash de contraseña, sesión.
- **[B3] Adoptar Alembic para migraciones** `could,infra`  
  Hoy se usa create_all. Antes de tener datos reales en PostgreSQL conviene migraciones.
