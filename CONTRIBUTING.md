# Cómo colaborar

## Primera vez
```bash
git clone <URL-del-repo> && cd plataforma-salas
make instalar && make test      # si pasan las pruebas, tu entorno está listo
```

## Flujo de trabajo (cada tarea)
1. Toma un **issue** del tablero y asígnatelo. Si no existe, créalo.
2. Actualiza `main` y crea una rama: `git switch main && git pull && git switch -c feat/B2-lambda-calibracion`
   - Prefijos: `feat/` (algo nuevo), `fix/` (arreglo), `docs/`, `test/`. Incluye el bloque (B1–B4) cuando aplique.
3. Haz commits chicos y claros, en español o inglés pero consistentes: `feat(B2): agrega sala fija al solver`.
4. Antes de subir: `make lint && make test`.
5. `git push -u origin <rama>` y abre un **Pull Request** hacia `main` (la plantilla te guía). Escribe `Closes #N`.
6. Pide revisión a **al menos 1 compañero**. El CI (GitHub Actions) debe estar verde. Quien revisa no es quien escribió el código.
7. Merge con **Squash and merge** y se borra la rama.

## Reglas
- **Nadie sube directo a `main`.**
- Un PR = una cosa. Si pasa de ~400 líneas, pártelo.
- Si cambias el motor (`app/engine/`), las pruebas PA-01…PA-04 deben seguir pasando (son la regresión del ATP).
- Nunca subas contraseñas, `.env` ni datos reales de estudiantes. Los datos reales de la secretaría viven **fuera** del repo (carpeta compartida privada).
- Una prueba ATP que falla se reporta con la plantilla **Falla en prueba de aceptación**, se corrige y se repite solo esa prueba.

## Evitar conflictos
- Cada bloque tiene su carpeta; si dos personas tocan el mismo archivo, avísense en el issue.
- `git pull --rebase origin main` seguido antes de abrir el PR.

## Estructura
```
app/engine/       B2 motor CP-SAT (sin dependencias web)
app/validacion.py B1 validación de planillas
app/routers/      B3/B4 API
app/templates/    interfaz web
scripts/          datos de ejemplo, placas QR, comparación A/B con la asignación manual
tests/            pruebas ATP automáticas
docs/             ATP, arquitectura, backlog
```
