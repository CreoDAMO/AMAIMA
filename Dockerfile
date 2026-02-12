FROM node:20-slim

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install backend dependencies
RUN cd amaima/backend && pip3 install --break-system-packages -r requirements.txt

# Install frontend dependencies and build
RUN cd amaima/frontend && npm install && npm run build

# Set default environment
ENV BACKEND_URL=http://localhost:8000
ENV PORT=5000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 5000

CMD ["/app/start.sh"]
