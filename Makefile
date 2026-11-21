.PHONY: instalar test lint correr ejemplo docker
instalar:   ## crea .venv e instala dependencias
	python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
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
