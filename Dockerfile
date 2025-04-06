# docker build -t jafber/frogwatch-front .
# docker run --rm -p 3000:80 jafber/frogwatch-front

FROM nginx:alpine
COPY /front /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]