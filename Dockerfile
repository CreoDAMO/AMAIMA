FROM python:3.11-slim-bookworm AS base

RUN apt-get update && apt-get install -y \
    curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN cd amaima/backend && pip install --no-cache-dir -r requirements.txt

ARG DATABASE_URL=""
ARG STRIPE_SECRET_KEY=""
ARG NVIDIA_API_KEY=""
ENV DATABASE_URL=${DATABASE_URL}
ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
ENV NVIDIA_API_KEY=${NVIDIA_API_KEY}

RUN cd amaima/frontend && npm install && npm run build

ENV BACKEND_URL=http://localhost:8000
ENV PORT=5000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 5000 8000

CMD ["/app/start.sh"]
