export PYTHONPATH=/bas
export FLASK_APP=wsgi_handler:app
if [ -f ${BAS_DB_PWD_FILE} ]; then
    export BAS_DB_PWD=$(cat ${BAS_DB_PWD_FILE})
fi
