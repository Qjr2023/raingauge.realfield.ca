# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
# Optional: serve under a path and/or call the API through a same-origin proxy (self-hosted build).
ARG VITE_BASE=/
ARG VITE_API_BASE_URL=
ENV VITE_BASE=$VITE_BASE VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Serve stage (Cloud Run listens on PORT, default 8080)
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "serve -s dist -l $PORT"]
