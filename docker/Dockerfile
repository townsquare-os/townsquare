FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy in package metadata + source first so the layer caches when only
# code changes.
COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir -e ".[google,all]"

COPY docker/entrypoint.sh /usr/local/bin/townsquare-entrypoint
RUN chmod +x /usr/local/bin/townsquare-entrypoint

EXPOSE 8000

ENTRYPOINT ["townsquare-entrypoint"]
