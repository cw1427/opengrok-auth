FROM python:3.6.8-alpine3.8

# Copy in your requirements file
COPY ./docker/gosu /usr/local/bin/

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step. Correct the path to your production requirements file, if needed.
ENV PYTHON_PIP_VERSION 9.0.1
ENV USER authapp
ENV CONFIG_ENV config_dev.py
ENV GOSU_USER 0:0
ENV GOSU_CHOWN /authapp
RUN echo https://mirrors.ustc.edu.cn/alpine/v3.8/main > /etc/apk/repositories; \
    echo https://mirrors.ustc.edu.cn/alpine/v3.8/community >> /etc/apk/repositories
RUN set -ex \
    && adduser -D -S -h /authapp -s /bin/sh -G ping ${USER} \
    && apk add --no-cache --repository https://mirrors.ustc.edu.cn/alpine/v3.8/main --repository https://mirrors.ustc.edu.cn/alpine/v3.8/community  --allow-untrusted  --virtual .build-deps \
            libldap\
            gcc \
            make \
            openldap-dev \
            zlib-dev \
            libc-dev \
            gd-dev\
            musl-dev \
            linux-headers \
            pcre-dev \
            python-dev \
            mariadb-dev \
            mariadb-client \
            libev \
            libxml2-dev \
            libxslt-dev \
    && chmod +x /usr/local/bin/gosu
    #&& gosu nobody true \
COPY ./docker/requirements.txt ./docker/entrypoint.sh ./docker/uwsgi.ini  /authapp/
RUN set -ex \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pip install --no-cache-dir -r /authapp/requirements.txt"
RUN rm -rf /authapp/requirements.txt
COPY  . /authapp
COPY fab_manager_overwrite/flask_appbuilder /usr/local/lib/python3.6/site-packages/flask_appbuilder

RUN chmod +x /authapp/entrypoint.sh
WORKDIR /authapp
VOLUME /authapp/logs
VOLUME /authapp/flask_session
# uWSGI will listen on this port
EXPOSE 8082
ENTRYPOINT ["sh","/authapp/entrypoint.sh"]
# Start supervisorctl
CMD ["uwsgi", "--ini", "/authapp/uwsgi.ini", "--die-on-term"]
