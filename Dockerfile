FROM node:20-alpine

WORKDIR /app

# Copy package definition
COPY package.json ./

# Copy core files
COPY server.js worker.js ./

# Create credentials directory
RUN mkdir -p /app/credentials

# Expose default port
EXPOSE 8787

# Environment variables default
ENV PORT=8787 \
    API_KEY=freebuff-default-key \
    RELAY_URL="" \
    FREEBUFF_DEBUG=false

CMD ["node", "server.js"]
