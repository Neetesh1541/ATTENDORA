# ATTENDORA Frontend Production Dockerfile
# Stage 1: Build static distribution
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency specifications
COPY package.json ./

# Install dependencies (use npm install)
RUN npm install

# Copy application sources
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:1.25-alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose standard HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
