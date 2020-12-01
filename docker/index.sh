#!/bin/bash

URL_ROOT="${URL_ROOT#/}"
URL_ROOT="${URL_ROOT%/}"

LOCKFILE=/opengrok/${URL_ROOT}-opengrok-indexer
URI="http://localhost:8080/${URL_ROOT}"
# $OPS can be overwritten by environment variable
OPS=${INDEXER_FLAGS:='-H -P -S -G'}

if [ -f "$LOCKFILE" ]; then
    date +"%F %T Indexer still locked, skipping indexing"
    exit 1
fi

touch $LOCKFILE

#if [ -z $NOMIRROR ]; then
#    date +"%F %T Mirroring starting"
#    opengrok-mirror --all --uri "$URI"
#    date +"%F %T Mirroring finished"
#fi

mkdir -p /opengrok/src/${URL_ROOT} /opengrok/data/${URL_ROOT}
# if not exists include part cp them
if [ ! -f "/opengrok/data/${URL_ROOT}/body_include" ]; then
    cp /opengrok/body_include /opengrok/data/${URL_ROOT}/.
fi
if [ ! -f "/opengrok/data/${URL_ROOT}/header_include" ]; then
    cp /opengrok/header_include /opengrok/data/${URL_ROOT}/.
fi

date +"%F %T Indexing starting"
opengrok-indexer \
    -a /opengrok/lib/opengrok.jar -- \
    -s /opengrok/src/${URL_ROOT} \
    -d /opengrok/data/${URL_ROOT} \
    --remote on \
    -W /opengrok/etc/configuration_${URL_ROOT}.xml \
    -U "$URI" \
    $OPS \
    $INDEXER_OPT "$@"
date +"%F %T Indexing finished"

rm -f $LOCKFILE
