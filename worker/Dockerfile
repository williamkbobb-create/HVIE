FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV QT_QPA_PLATFORM=offscreen
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       colmap=3.9.1-2build2 \
       python3 \
       python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
RUN useradd --system --uid 10001 --create-home hvie \
    && mkdir -p /data \
    && chown -R hvie:hvie /app /data

USER hvie
EXPOSE 8787

CMD ["python", "-m", "app.runner"]
