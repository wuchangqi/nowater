#coding: utf-8
import datetime
import psycopg2

from settings import DATABASE_ARGS

QUERY_SQL = '''select id, type, url, last_update_url, last_update_floor, update_interval, last_update_time, status
from nowater_novel where status in (0, 2, 4)
order by status
for update'''
COMMON_UPDATE = """update nowater_novel set status=4 where status = 1 and now() - last_update_time > interval '30m'"""
QUERY_BY_ID_SQL = '''select id, type, url, last_update_url, last_update_floor from nowater_novel where id = %s'''
QUERY_STATUS_URL = '''select status from nowater_novel where id = %s'''
UPDATE_STATUS = '''update nowater_novel set status = %s where id = %s'''
UPDATE_FLOOR = '''update nowater_novel set last_update_floor = %s where id = %s'''
UPDATE_LASTUPDATE = '''update nowater_novel set last_update_time = now(),last_update_url=%s where id = %s'''
PAGE_INFO = '''select page,word_count from page_info where id = %s'''
UPDATE_PAGE_INFO = '''update page_info set page=%s, word_count=%s where id =%s'''
INSERT_PAGE_INFO = '''insert into page_info (id) values (%s);'''
INCR_INTERVAL = '''update nowater_novel set update_interval = update_interval+10 where id = %s and update_interval <= 110'''
DECR_INTERVAL = '''update nowater_novel set update_interval = update_interval-10 where id = %s and update_interval >= 20'''
UPDATE_SUMMARY = '''update profile set summary = %s where id = %s'''
QUERY_SUMMARY = '''select summary from profile where id = %s limit 1'''

class BaseDB(object):
    """
    操作数据库
    """
    def __init__(self):
        self.cx = psycopg2.connect(**DATABASE_ARGS)
        self.cx.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cu = self.cx.cursor()
        # 把有问题的置成4
        self.cu.execute(COMMON_UPDATE)
        
    def close(self):
        self.cx.close()
    
    def commit(self):
        self.cx.commit()
    
    def get_novel_list(self):
        """
        获得需要更新的小说
        """
        self.cu.execute(QUERY_SQL)
        ret = self.cu.fetchall()
        todo = []
        for n in ret:
            if n[-1] in (0, 4):
                todo.append(n[:5])
            else:
                lut = n[-2].replace(tzinfo=None)
                interval = datetime.datetime.now() - lut
                if interval.seconds/60 > n[-3]:
                    todo.append(n[:5])
        return todo
    
    def get_novel_by_id(self, id):
        """
        根据id获得小说信息
        """
        self.cu.execute(QUERY_BY_ID_SQL, (id,))
        return self.cu.fetchone()
    
    def get_status(self, id):
        """
        查询status
        """
        self.cu.execute(QUERY_STATUS_URL, (id,))
        ret = self.cu.fetchone()
        return ret[0] if ret else 1
    
    def modify_status(self, id, status):
        """
        修改状态
        """
        self.cu.execute(UPDATE_STATUS, (status, id))
        
    def update_url(self, id, url):
        """
        修改最后更新时间，以及最后更新页面
        """
        self.cu.execute(UPDATE_LASTUPDATE, (url, id))
    
    def update_floor(self, id, floor):
        """
        修改最后更新的楼层
        """
        self.cu.execute(UPDATE_FLOOR, (floor, id))
        
    def get_page_info(self, id):
        """
        查询分页所用的信息
        """
        self.cu.execute(PAGE_INFO, (id, ))
        ret = self.cu.fetchone()
        if not ret:
            self.cu.execute(INSERT_PAGE_INFO, (id, ))
            return self.get_page_info(id)
        return ret
    
    def update_page_info(self, id, page, word_count):
        """
        修改分页信息
        """
        self.cu.execute(UPDATE_PAGE_INFO, (page, word_count, id))
        
    def incr_interval(self, id):
        """
        增加时间间隔，每次加十分钟，不超过60
        """
        self.cu.execute(INCR_INTERVAL, (id,))
        
    def decr_interval(self, id):
        """
        降低时间间隔，每次减十分钟，不低于10
        """
        self.cu.execute(DECR_INTERVAL, (id,))
    
    def get_summary_flag(self, id):
        """
        获得是否需要更新SUMMARY
        """
        self.cu.execute(QUERY_SUMMARY, (id,))
        result = self.cu.fetchone()
        return not bool(result[0])
    
    # 处理摘要
    def update_summary(self, id, summary):
        self.cu.execute(UPDATE_SUMMARY, (summary, id))
#        self.cu.execute('''insert into profile (id, summary) values (%s, %s)''', (id, summary))

if __name__ == "__main__":
    # 处理文章标签
    db = BaseDB()
#    db.cu.execute("select id from nowater_novel where status !=1")
#    result = [x[0] for x in db.cu.fetchall()]
#    
#    print result
#    import re
#    import hashlib
#    from BeautifulSoup import BeautifulSoup
#    def get_novel_html_path(id, page):
#        """
#        获得小说的静态地址
#        """
#        id = str(id)
#        hashvalue = hashlib.md5(id).hexdigest()
#        return "%s/%s/%s/%s.html" % ("novels", hashvalue[:2], id, page)
#    
#    def get_summary(content):
#        soup = BeautifulSoup(content)
#        for x in soup.contents:
#            if hasattr(x, "get") and x.get("class") == 'content_main':
#                [ t.extract() for t in x.findAll("span", {"class": "floor"}) ]
#                content = strip_tag(unicode(x.renderContents(), 'utf-8'))
#                if len(content) <= 20:
#                    continue
#                return content[:100]
#        return ""
#    
#    TAG_RE = re.compile(ur"<[^>]+>|\s|　|&nbsp;")
#    def strip_tag(content):
#        """
#        忽略标签
#        """
#        return TAG_RE.sub("", content)
#    
#    for id in result:
#        print id, get_novel_html_path(id, 1)
#        try:
#           content = open(get_novel_html_path(id, 1), 'r').read()
#        except:
#           continue
#        summary = get_summary(content)
#        db.update_summary(id, summary)
#    db.cx.commit()
