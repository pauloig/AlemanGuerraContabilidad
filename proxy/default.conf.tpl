server {
    listen ${LISTEN_PORT};

    proxy_connect_timeout 1800s;
    proxy_send_timeout 1800s;
    proxy_read_timeout 1800s;
    send_timeout       1800s;
    fastcgi_send_timeout 1800s;
    fastcgi_read_timeout 1800s;

    location /static {
        alias /vol/static;

        proxy_connect_timeout 1800s;
        proxy_send_timeout 1800s;
        proxy_read_timeout 1800s;
        send_timeout       1800s;
        fastcgi_send_timeout 1800s;
        fastcgi_read_timeout 1800s;
    }

    location / {
        uwsgi_read_timeout 1800s;
        uwsgi_send_timeout 1800s;
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    30M;

        proxy_connect_timeout 1800s;
        proxy_send_timeout 1800s;
        proxy_read_timeout 1800s;
        send_timeout       1800s;
        fastcgi_send_timeout 1800s;
        fastcgi_read_timeout 1800s;
    }
}