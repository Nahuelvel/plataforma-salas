.PHONY: instalar test lint correr ejemplo docker
# OR-Tools aún no publica paquetes para Python 3.14+. Usa 3.12 o 3.13:  make instalar PYTHON=python3.13
PYTHON ?= python3
instalar:   ## crea .venv e instala dependencias (Python 3.12 o 3.13)
	@$(PYTHON) -c "import sys; assert (3,12) <= sys.version_info[:2] <= (3,13), 'Se necesita Python 3.12 o 3.13 (tienes ' + sys.version.split()[0] + '). Usa: make instalar PYTHON=python3.13'"
	$(PYTHON) -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
test:       ## pruebas ATP automáticas (PA-01…PA-05 y QR)
	.venv/bin/python -m pytest
lint:
	.venv/bin/ruff check .
correr:     ## servidor local con SQLite en http://localhost:8000
	.venv/bin/uvicorn app.main:app --reload
ejemplo:    ## regenera las planillas de ejemplo
	.venv/bin/python scripts/generar_datos_ejemplo.py
docker:     ## levanta API + PostgreSQL (requiere .env)
	docker compose up --build
