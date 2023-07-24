#!/bin/sh

# If log file does not exist, create it.
if [ ! -f ${LOG_DIR}/${TG_SESSION_NAME}.log ]; then
    mkdir -p ${LOG_DIR}
    touch ${LOG_DIR}/${TG_SESSION_NAME}.log
    echo "Created log file."
fi

python kasetlyricsbot.py & tail -f ${LOG_DIR}/${TG_SESSION_NAME}.log
