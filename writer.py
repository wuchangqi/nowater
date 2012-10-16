#coding: utf-8
import os
import hashlib

from common import strip_tag
from common import notify_page

BASE = os.path.dirname(os.path.abspath(__file__))

def get_path(id):
    """
    生成该小说应该的路径
    """
    hashvalue = hashlib.md5(id).hexdigest()
    return os.path.join(BASE, "novels", hashvalue[:2], id)

class BaseWriter(object):
    """
    生成脱水小说的类，带分页
    """
    WORD_PERPAGE = 10000
    SUMMARY_FLAG = False
    
    def __init__(self, id, db):
        """
        该类需要做的事情：
            判断html是否存在，如果不存在，新建该文件。
            如果存在，找到上一次的checkpoint，进行追加。
        """
        self.id = str(id)
        self.db = db
        self.path = get_path(self.id)
        # 路径不存在则创建路径
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
        # 查询数据库取得那什么
        self.page, self.word_count = self.db.get_page_info(self.id)
        self.make_file(init=True)
        
        self.SUMMARY_FLAG = self.db.get_summary_flag(self.id)
        self.SEND_LAST_PAGE = False
        
    def make_file(self, init=False):
        """
        生成self.file用于文件写入
        """
        if not init:
            self.file.close()
        filepath = os.path.join(self.path, "%s.html" % self.page)
        self.file = open(filepath, "a")        
    
    def write_content(self, page):
        """
        写入正文内容
        """
        first_flag = True
        self.SEND_LAST_PAGE = True
        for each in page["content"]:
            _len = len(each["content"])
            
            # 判断是否写入摘要
            try: real_content = unicode(each["content"], 'utf-8', 'ignore')
            except: real_content = each["content"]
            real_content = strip_tag(real_content)
            if self.SUMMARY_FLAG and len(real_content) > 33:
                self.db.update_summary(self.id, real_content[:100])
                self.SUMMARY_FLAG = False
            
            if self.word_count + _len > self.WORD_PERPAGE and self.word_count > self.WORD_PERPAGE*0.75:
                # 修改页数
                self.db.update_page_info(self.id, self.page, self.word_count)
                notify_page(self.id, "o_%s" % self.page)
                
                self.page += 1
                self.word_count = 0
                self.make_file()
            if first_flag:
                self.file.write('''
        <div class="content_top">
        原帖第 %(page)s 页：<a href="%(url)s" target="_blank">查看该页内容</a>
        </div>
                ''' % page)
                first_flag = False               
            self.file.write('''
            <div class="content_main">
                <a name="%(floor)s"></a>
                %(content)s
                <span class="floor"><a href="#%(floor)s" onclick="alert('设置完成，请添加收藏夹吧！')">[设为书签]</a></span>
            </div>
            ''' % each)
            self.word_count += _len
        
        # 第一次写入如果是第一页的话需要强制翻页
        if self.page == 1:
            self.page += 1
            self.word_count = 0
            self.make_file()

            notify_page(self.id, "o_%s" % self.page)
        
        # 内存问题
        self.file.flush()
    
    def close(self):
        """
        关闭文件
        """
        if self.SEND_LAST_PAGE:
            notify_page(self.id, "o_%s" % self.page)
        self.db.update_page_info(self.id, self.page, self.word_count)
        self.file.close()
