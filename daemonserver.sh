#!/bin/bash
SCRIPTNAME=daemonserver.sh
PIDFILE=fts_server.pid
PYTHONCMD=/usr/bin/python
do_start() {
    $PYTHONCMD ftsNetMain.py
}
do_stop() {
    kill `cat $PIDFILE` || echo -n "fts server not running"
}
case "$1" in
    start)
        do_start
    ;;
    stop)
        do_stop
    ;;
    restart)
        do_stop
        do_start
    ;;
    *)
    echo "Usage: $SCRIPTNAME {start|stop||restart}" >&2
    exit 3
    ;;
esac
exit
