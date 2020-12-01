FROM tomcat:9-jdk11

# Copy in your requirements file
# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step. Correct the path to your production requirements file, if needed.
ENV PYTHON_PIP_VERSION 9.0.1
ENV OPENGROK_USER opengrok
ENV GOSU_USER 0:0
ENV GOSU_CHOWN /opengrok
ENV SRC_ROOT /opengrok/src
ENV DATA_ROOT /opengrok/data
ENV URL_ROOT /source
ENV CATALINA_HOME /usr/local/tomcat
ENV CATALINA_BASE /usr/local/tomcat
ENV CATALINA_TMPDIR /usr/local/tomcat/temp
ENV PATH $CATALINA_HOME/bin:$PATH
ENV CLASSPATH /usr/local/tomcat/bin/bootstrap.jar:/usr/local/tomcat/bin/tomcat-juli.jar
ENV OPENGROK_VERSION opengrok-1.5.7.tar.gz
ENV REINDEX 0

RUN apt-get update \
  && apt-get install -y git python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python
  #&& pip3 install --upgrade pip

# compile and install universal-ctags
RUN apt-get install -y pkg-config autoconf build-essential && \
    git clone https://github.com/universal-ctags/ctags /root/ctags && \
    cd /root/ctags && ./autogen.sh && ./configure && make && make install && \
    apt-get remove -y autoconf build-essential && \
    apt-get -y autoremove && apt-get -y autoclean && \
    cd /root && rm -rf /root/ctags
            
COPY ./docker/$OPENGROK_VERSION /
COPY ./docker/gosu /usr/local/bin/
COPY ./docker/requirements.txt /
RUN mkdir -p /opengrok /opengrok/etc /opengrok/data /opengrok/src && \
    tar -zxvf /$OPENGROK_VERSION -C /opengrok --strip-components 1 && \
    rm -f /opengrok.tar.gz
RUN set -ex \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "python -m pip install -i --no-cache-dir /opengrok/tools/opengrok-tools.tar.gz" \
    && /bin/sh -c "python -m pip install -r /requirements.txt"
COPY ./docker/*.sh ./docker/supervisord.conf ./docker/*_include ./docker/logo.png /opengrok/
RUN chmod +x /opengrok/*.sh /usr/local/bin/gosu
WORKDIR /opengrok
VOLUME /usr/local/tomcat/logs
VOLUME /opengrok/src
VOLUME /opengrok/data
VOLUME /opengrok/etc
EXPOSE 8080
# uWSGI will listen on this port
ENTRYPOINT ["sh","./entrypoint.sh"]
# Start supervisorctl
CMD ["/usr/local/bin/supervisord"]
