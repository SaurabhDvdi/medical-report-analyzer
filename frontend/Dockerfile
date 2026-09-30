# Multi-Stage Build Dockerfile for Frontend SPA
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code and build production bundle
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# Nginx Production Stage
FROM nginx:alpine AS runner

# Copy customized Nginx configuration with reverse proxy, SPA routing, and SSE streaming
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend static assets to Nginx html folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
