FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ENV NEXT_PUBLIC_API_BASE=http://localhost:8000

EXPOSE 3000
CMD ["npm", "run", "dev"]
