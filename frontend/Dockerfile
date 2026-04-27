# ─────────────────────────────────────────────
#  TaskForge Frontend — Production Dockerfile
#  Multi-stage: build + serve with nginx
# ─────────────────────────────────────────────

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --silent
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
