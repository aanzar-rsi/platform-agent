FROM node:22-alpine

WORKDIR /app

ARG VITE_API_URL=http://localhost:5000
ARG VITE_WS_URL=ws://localhost:5000
ENV VITE_API_URL=$VITE_API_URL \
    VITE_WS_URL=$VITE_WS_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
