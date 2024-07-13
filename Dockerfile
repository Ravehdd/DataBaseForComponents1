# Используем Node.js как основу для сборки фронтенда
FROM node:latest

WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install
RUN chmod +x /node_modules/react-scripts
# Копируем все файлы фронтенда
COPY . .

# Собираем фронтенд приложение
CMD npm start
#RUN npm run build
#
## Второй этап Dockerfile на основе nginx для сервера фронта
#FROM nginx:1.21
#
## Копируем собранное фронтенд приложение в nginx
#COPY --from=build /app/build /usr/share/nginx/html
