#!/bin/bash

TEMP=`getopt --long -o "n:" "$@"`
eval set -- "$TEMP"
while true ; do
    case "$1" in
        -n )
            name=$2
            break
        ;;
        *)
            break
        ;;
    esac
done;

if [[ "${name}" = "" ]]
then
   echo "please input: -n <new app name>"
   exit 1
fi

export URL_ROOT=${name}

# default period for reindexing (in minutes)
if [ -z "$REINDEX" ]; then
    REINDEX=10
fi

if [[ "${URL_ROOT}" = *" "* ]]; then
    date +"%F %T Deployment path contains spaces. Deploying to root..."
    export URL_ROOT="/"
fi

# Remove leading and trailing slashes
URL_ROOT="${URL_ROOT#/}"
URL_ROOT="${URL_ROOT%/}"

if [ "${URL_ROOT}" = "" ]; then
    WAR_NAME="ROOT.war"
else
    WAR_NAME="${URL_ROOT//\//#}.war"
fi

if [ ! -f "/usr/local/tomcat/webapps/${WAR_NAME}" ]; then
    date +"%F %T Deployment path changed. Redeploying..."
    # Delete old deployment and (re)deploy
    rm -rf /usr/local/tomcat/webapps/${WAR_NAME}
    rm -rf /usr/local/tomcat/webapps/${URL_ROOT}
    opengrok-deploy -c /opengrok/etc/configuration_${URL_ROOT}.xml \
            /opengrok/lib/source.war "/usr/local/tomcat/webapps/${WAR_NAME}"
    sleep 30
    # copy the customize logo into default/img path
    cp /opengrok/logo.png /usr/local/tomcat/webapps/${URL_ROOT}/default/img/.
fi

indexer(){
    if [[ ! -d /opengrok/data/${URL_ROOT}/index ]]; then
        /opengrok/index.sh --noIndex
        # Perform initial indexing.
        /opengrok/index.sh
        date +"%F %T Initial reindex finished"
        date +"%F %T Restart tomcat for new application created."
        catalina.sh stop
        sleep 5
        catalina.sh start
    else
        echo "index exists, reindex one time no need restart"
        /opengrok/index.sh
    fi

    # Continue to index every $REINDEX minutes.
    if [ "$REINDEX" == "0" ]; then
        date +"%F %T Automatic reindexing disabled"
        return
    else
        date +"%F %T Automatic reindexing in $REINDEX minutes..."
    fi
    while true; do
        sleep `expr 60 \* $REINDEX`
        /opengrok/index.sh
    done
}

# Start all necessary services.
indexer
