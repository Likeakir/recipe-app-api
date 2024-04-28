server{
    listen ${LISTEN_PORT};

    location /static{
        alias /vol/static;
    }

    location / {
        uwsigi_pass          ${APP_HOST}.${APP_PORT};
        include              /etc/nginx/uswigi_params;
        client_max_body_size 10M;
    }
}