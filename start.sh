#!/bin/bash
usage="Usage: $0 [start|stop|restart]"

function start(){
    /home/piglei/bin/twistd -y long_polling.py --reactor=poll --pidfile=long_polling.pid --logfile=long_polling.log
}
function stop(){
    kill -KILL `cat long_polling.pid`
}
function restart(){
    stop &&
    sleep 1
    while  ! start ; do
        echo "failed, retrying..."
        sleep 10
    done
    echo "retart finished"
}

case $1 in
    start ) start ;;
    stop )  stop ;;
    restart ) restart ;;
    * ) echo $usage
        exit 1 ;;
esac
