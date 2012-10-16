#coding: utf-8
import os
import sys
import stat
import time
import threading
import traceback
import Queue

#from utils import BaiduWriter
from writer import BaseWriter
from settings import log, lockfile

from crawlers.baidu_crawler import BaiduZhibo
from crawlers.tianya_crawler import TianyaLZ
from crawlers.douban_crawler import DoubanZhibo

from basedb import BaseDB
from common import notify_page

THREADS_COUNT = 8
PAGES_PER_RUN = 100

TYPE_TO_CRAWLER = {
    "baidu": BaiduZhibo,
    "tianya": TianyaLZ,
    "douban": DoubanZhibo
}
G_LOCK = {}

def ready_work(novel, db):
    """
    准备工作，用于twisted中的堵塞
    """
    global G_LOCK
    id, type, main_url, url, last_floor = novel
    
    now_status = db.get_status(id)
    if now_status in (1, 3):
        return False
    G_LOCK.setdefault(id, threading.RLock())
    G_LOCK[id].acquire()
    
    db.modify_status(id, 1)
    log.info("novel %s %s start." % (id, type))
    return True

def do_work(novel, db):
    """
    执行工作
    """
    id, type, main_url, url, last_floor = novel

    crawler = TYPE_TO_CRAWLER[type]
    source = crawler(main_url, url=url, html=True, floor=last_floor)
    writer = BaseWriter(id, db)
    floor = None
    eachpage = None
    i = 0
    # 控制每次抓取的页数
    for eachpage in source:
#        if i >= PAGES_PER_RUN:
#            break
        notify_page(id, "r_%s" % eachpage["page"])
        
        i += 1
        # 修改最后更新url
        db.update_url(id, eachpage["url"])
#            gc.collect()
        if not eachpage["content"]:
            continue
        floor = max([x["floor"] for x in eachpage["content"]])
        writer.write_content(eachpage)
        # 修改最后更新楼层
        db.update_floor(id, floor)
    
    # 检测这次是不是只跑了一页
    # 修改间隔时间
    if eachpage["url"] == url:
        db.incr_interval(id)
    else:
        db.decr_interval(id)
    # 完成
    writer.close()
    db.modify_status(id, 2)
    notify_page(id, "end")
    log.info("novel %s ended." % id)
    try: G_LOCK[id].release()
    except: pass
    
if __name__ == "__main__":
    # 检查锁
    if os.path.exists(lockfile):
        last_access_time = os.stat(lockfile)[stat.ST_MTIME]
        if (time.time() - last_access_time < 3600 * 12):        
            log.info("locked, exit")
            sys.exit()
    open(lockfile, "w").close()
    
#    # Enable automatic garbage collection.
#    gc.enable()
#    # Set the garbage collection debugging flags.
#    gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
    
    log.info("start")
    q = Queue.Queue()
    
    def worker():
        db = BaseDB()
        while q.qsize():
            novel = q.get()
            try:
                if ready_work(novel, db):
                    notify_page(novel[0], "start")
                    do_work(novel, db)
            except Exception, e:
                log.error("%s: %s" % (novel[0], traceback.format_exc()))
                db.modify_status(novel[0], 4)
            db.commit()
            q.task_done()
    
    # 插入任务
    db = BaseDB()
    novel_list = db.get_novel_list()
    log.info("novel count %s", len(novel_list))
    for novel in novel_list:
#        db.modify_status(novel[0], 1)
        q.put(novel)
#    db.commit()
    db.close()
    del db
    
    for i in range(min(q.qsize(), THREADS_COUNT)):
        t = threading.Thread(target=worker)
        t.setDaemon(True)
        t.start()
        
    q.join()
    log.info("end")
    os.remove(lockfile)
