#coding: utf-8
"""
天涯只看楼主提取脚本
@author:piglei2007@gmail.com
@version:1.0

天涯包括publicforum和techforum两种，处理方式各不一样。
"""
import sys
sys.path.append("../../nowater")
import re
import time
import datetime
import urllib2
import urlparse
import socket
socket.setdefaulttimeout(10)

from BeautifulSoup import BeautifulSoup

from settings import log
from common import remove_br as _br
from common import reconnecting_urlopen

DIGIT_RE = re.compile(r"\d+")
DATE_RE = re.compile(r"(?:发表|回复)日期：([^<]+)")
AD_RE = re.compile(r"my.tianya.cn")

class TianyaLZ(object):
    """
    可迭代的对象,不停返回下一页含有给定username的内容（默认为楼主）
    返回格式:
        字典：{
            "url": "..."        #当前链接地址
            "page": 5           #当前页数
            "content": [...]    #列表，里面有当前页每一个指定username的发言内容
        }
         
    参数：
        main_url: 贴子地址
        url:    开始抓取的地址
        obj_name:   需要抓取的用户昵称，默认为楼主
        limit:  限定抓取页面的数量，默认无限制
        html:   设定输出格式，True不做处理，False替换换行符、空格
    """
     
    def __init__(self, main_url, url="", obj_name=None, limit=0, html=True, floor=0):
        self.limit = limit
        self.counter = 0
        self.html = html
        self.floor = floor
        self.nowurl = url or main_url
        self.starturl = url or main_url
        self.page = 1
        
        # 天涯目前贴子分两类，处理规则各不相同
        # techforum、publicforum
        self.thread_type = self.starturl.split("/")[3]
        
        content = reconnecting_urlopen(main_url, retry=100).decode("gbk", "ignore")
        log.info("content %s %s %s" % (len(content), type(content), content[:100]))
        soup = BeautifulSoup(content)
        
        # 处理obj_name
        self.obj_name = obj_name
        if not self.obj_name:
            # 获得楼主昵称
            if self.thread_type == "techforum":
                self.obj_name = soup.find("div", {"class": "vcard"}).find("a", target="_blank").renderContents()
            else:
                self.obj_name = self.get_firstauthor(soup)
    
    def next(self):
        if (self.limit and self.counter == self.limit) or (self.nowurl is None):
            raise StopIteration

        result = {}
        result["url"] = self.nowurl
        result["content"] = []
        try:
            content = reconnecting_urlopen(self.nowurl).decode("gbk", "ignore")
        except Exception, e:
            raise StopIteration
        soup = BeautifulSoup(content)
        # 此处根据self.thread_type的不同来进行不同的操作
        if self.thread_type == "techforum":
            pagediv = soup.find("div", id="cttPageDiv")
            if pagediv:
                self.page = int(pagediv.find("em", {"class": "current"}).renderContents())
            else:
                self.page = 1
            posts = soup.findAll("div", {"class": "item"})
            for post in posts:
                username = self.get_username(post)
                if username is None:
                    continue
                if username == self.obj_name:
                    floor, content = self.parse_post(post)
                        
                    # 判断楼层数
                    if floor > self.floor or floor  == 0:
                        result["content"].append({
                            "floor": floor,
                            "content": _br(content),
                        })
        else:
            pagediv = soup.find("div", id="pageDivTop")
            if pagediv:
                self.page = int(pagediv.find("em", {"class": "current"}).renderContents())
            else:
                self.page = 1
            firstauthor = self.get_firstauthor(soup)
            content = soup.find("table", id="firstAuthor").renderContents()
            posts = soup.find("div", id="pContentDiv")
            
            # 假的floor，为时间戳
            floor = self.mk_floor(content)
                        
            if firstauthor == self.obj_name:
                content = posts.find("div", {"class": "post"})
                self.process_content(content)
                content = content.renderContents()
                if floor > self.floor:
                    result["content"].append({
                        "floor": floor,
                        "content": _br(content),
                    })
            
            for post in posts.findAll("table"):
                _username = post.find("a", target="_blank")
                if not _username:
                    continue
                username = _username.renderContents()
                if username == self.obj_name:
                    content = post.findNextSibling("div", {"class": "post"})
                    self.process_content(content)
                    content = content.renderContents()
                    
                    # 假的floor，为时间戳
                    floor = self.mk_floor(post.renderContents())
                    if floor > self.floor:
                        result["content"].append({
                            "floor": floor,
                            "content": _br(content),
                        })
                        
        result["page"] = self.page
        self.nowurl = self.get_nexturl(soup)
        self.counter += 1
        return result
         
    def __iter__(self):
        return self
     
    def get_username(self, post):
        """
        获得用户姓名
        """
        _name = post.find("div", {"class": "vcard"})
        return _name.find("a", target="_blank").renderContents() if _name else None
     
    def parse_post(self, post):
        """
        返回楼数和内容
        """
        floor = post.find("span", {"class": "floor"}).next
        floor = int(floor) if floor.isdigit() else 0
        
        content = post.find("div", {"class": "post"})
        self.process_content(content)
        content = content.renderContents()
        return int(floor), content
    
    def get_firstauthor(self, soup):
        """
        thread_type为publicform时，用于获得firstauthor
        """
        return soup.find("table", id="firstAuthor").find("a", target="_blank").renderContents()
 
    def get_nexturl(self, soup):
        """
        从页面获得下一页url
        """
        next = soup.find(text=u"下一页")
        if next:
            return urlparse.urljoin(self.starturl, next.parent.get("href")).encode("utf-8")
        return None
    
    def process_content(self, soup):
        """
        去除不需要的内容
        """
        try:
            [t.extract() for t in soup.findAll("div", {"class": "post-jb"})]
            [t.extract() for t in soup.findAll("span", {"class": "fromwap"})]
            [t.extract() for t in soup.findAll("a", href=AD_RE)]
        except:
            pass
    
    @staticmethod
    def mk_floor(content):
        """
        在publicform模式下，生成假的floor
        """
        try:
            _date = DATE_RE.search(content).group(1)
            _date = _date.replace("　", " ")
            return int(time.mktime(datetime.datetime.strptime(_date, "%Y-%m-%d %H:%M:%S").timetuple()))
        except:
            return 0

if __name__ == '__main__':
    bz = TianyaLZ("http://www.tianya.cn/publicforum/content/free/1/2305612.shtml", html=True, limit=0)
    for x in bz:
        print len(x["content"])
        print x["url"], x["page"]
        for y in x["content"]:
            print y["floor"]
            print y["content"]
            break
        break
