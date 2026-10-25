# Laia
#   make run            arranca el backend en http://localhost:8000
#   make run flutter    arranca la app en el móvil conectado
#   make test           pasa los tests del backend
#   make llamada        Laia llama a tu negocio de prueba (con el backend en marcha)

SHELL := /bin/bash
VENV := source ../venv/bin/activate

.PHONY: run run-backend run-flutter flutter test llamada

ifneq ($(filter flutter,$(MAKECMDGOALS)),)
run: run-flutter
else
run: run-backend
endif

flutter:
	@:

run-backend:
	@cd backend && $(VENV) && set -o pipefail && { \
		echo "== Instalando dependencias" && \
		pip install -q "poetry>=2,<3" && poetry install --no-root -q && \
		echo "== Preparando la base de datos" && \
		python manage.py migrate --noinput && \
		python manage.py ensure_admin && \
		python manage.py check_config && \
		python manage.py setup_telegram && \
		echo "== Laia en http://localhost:8000" && \
		uvicorn core.asgi:application --port 8000 --reload --reload-dir . ; \
	} 2>&1 | tee ../arranque_laia.log

run-flutter:
	@cd app && flutter pub get && flutter run

test:
	@cd backend && $(VENV) && python -m pytest -q

llamada:
	@cd backend && $(VENV) && python manage.py llamada_prueba
