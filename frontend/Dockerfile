FROM node:20-alpine AS build
WORKDIR /web
ARG VITE_APP_BASE_PATH=/NotasCompensadas-FBL1/
ARG VITE_API_BASE_URL=/NotasCompensadas-FBL1/
ARG VITE_WS_BASE_URL=
ENV VITE_APP_BASE_PATH=$VITE_APP_BASE_PATH
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
RUN mkdir -p /usr/share/nginx/html/NotasCompensadas-FBL1
COPY --from=build /web/dist/ /usr/share/nginx/html/NotasCompensadas-FBL1/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
