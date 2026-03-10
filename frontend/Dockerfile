# Build stage
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Production stage – serve with nginx
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

ENV PORT=80 \
    NGINX_ENVSUBST_TEMPLATE_VARS=PORT

CMD ["nginx", "-g", "daemon off;"]
