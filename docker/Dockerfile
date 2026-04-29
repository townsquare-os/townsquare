FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir -e ".[google,all]"

EXPOSE 8000

CMD ["uvicorn", "townsquare.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
