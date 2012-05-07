#!/bin/bash
set -e
LOGFILE=/var/log/gunicorn/mugged.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=2
USER=bradmann
GROUP=bradmann
cd /apps/mugged/mugged
source ../venv/bin/activate
test -d $LOGDIR || mkdir -p $LOGDIR
exec ../venv/bin/gunicorn_django -w $NUM_WORKERS --user=$USER --group=$GROUP --log-level=debug --log-file=$LOGFILE 2>>$LOGFILE
