#coding: utf-8
import os
import logging
import psycopg2

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DATABASE_ARGS = {
    "host": "127.0.0.1",
    "port": "5432",
    "database": "piglei_nowater",
    "user": "piglei_nowater",
    "password": "zhulei@wf",    
}
cx = psycopg2.connect(**DATABASE_ARGS)
cu = cx.cursor()

def get_logger(loggername,filename):
    """
    获得log文件
    """
    log = logging.getLogger(loggername)
    hdlr = logging.FileHandler(filename,'a')
    
    fs = '%(asctime)s %(levelname)-5s %(message)s'
    fmt = logging.Formatter(fs)
    hdlr.setFormatter(fmt)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    return log
log = get_logger("main", os.path.join(PROJECT_PATH, "info.log"))

lockfile = os.path.join(PROJECT_PATH, ".lock")

NOTIFY_URL = "http://127.0.0.1:9000/progress"
