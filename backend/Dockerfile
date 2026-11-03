FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SKIP_VENV_REEXEC=true

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY backend/ .
COPY scripts/db_setup.py ./scripts/db_setup.py
COPY scripts/create_user.py ./scripts/create_user.py

EXPOSE 5000

CMD ["python", "main.py"]
