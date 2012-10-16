#coding: utf-8
"""
豆瓣直播贴提取脚本
@author:piglei2007@gmail.com
@version:1.0
"""
import re
import urllib2
import urlparse
import socket
socket.setdefaulttimeout(10)

from BeautifulSoup import BeautifulSoup
from common import remove_br as _br
from common import reconnecting_urlopen

from settings import log

DIGIT_RE = re.compile(r"\d+")
PN_RE = re.compile(r"[\?&]pn=(\d+)")
CONTENTP_RE = re.compile(r"post_content_\d+")
DOUBAN_PEOPLE = re.compile(r"http://www.douban.com/people/[^/]+/$")

class DoubanZhibo(object):
    """
    http://www.douban.com
    """
    ENCODING = "utf-8"
     
    def __init__(self, main_url, url="", obj_name=None, limit=0, html=False, floor=0):
        self.limit = limit
        self.counter = 0
        self.html = html
        self.floor = floor
        self.nowurl = url or main_url
        self.starturl = url or main_url
        
        # 处理obj_name
        self.obj_name = obj_name
        if not self.obj_name:
            # 获得楼主昵称
            content = reconnecting_urlopen(main_url, retry=100).decode(self.ENCODING, "ignore")
            log.info("content %s %s %s" % (len(content), type(content), content[:100]))
            soup = BeautifulSoup(content)
            first = soup.find("div", {"class": "topic-doc"})
            self.obj_name = self.get_username(first)
    
    def next(self):
        if (self.limit and self.counter == self.limit) or (self.nowurl is None):
            raise StopIteration
         
        self.page = self.get_page(self.nowurl)

        result = {}
        result["url"] = self.nowurl
        result["page"] = self.page
        result["content"] = []

        floor = (self.page - 1) * 100 + 1
        try:
            content = reconnecting_urlopen(self.nowurl).decode(self.ENCODING, "ignore")
            soup = BeautifulSoup(content)
        except Exception, e:
            raise StopIteration

        # 首页添加楼主的内容
        if self.page == 1 and floor > self.floor:
            _content = soup.find("div", {"class": "topic-doc"}).p.renderContents()
            result["content"].append({
                "floor": 1,
                "content": _br(_content)
            })

        posts = soup.findAll("div", {"class": "reply-doc"})
        for post in posts:
            floor += 1
            username = self.get_username(post)
            if username == self.obj_name:
                content = post.p.renderContents()
                 
                if not self.html:
                    cc = self.replace_htmltag(content)
                    
                # 判断楼层数
                if floor > self.floor:
                    result["content"].append({
                        "floor": floor,
                        "content": _br(content),
                    })
        self.nowurl = self.get_nexturl(soup)
        self.counter += 1
        self.page += 1
        return result
         
    def __iter__(self):
        return self
     
    def get_username(self, post):
        """
        获得用户姓名
        """
        return post.find("a", href=DOUBAN_PEOPLE).renderContents()
 
    def get_nexturl(self, soup):
        """
        从页面获得下一页url
        """
        next = soup.find(text=u"后页&gt;")
        if next and next.parent.name == "a":
            return urlparse.urljoin(self.starturl, next.parent.get("href")).encode("utf-8")
        return None

    def get_page(self, url):
        """
        根据get里面的start返回页数
        """
        if "?" in url:
            try:
                qs = url.rsplit("?", 1)[-1]
                return int(urlparse.parse_qs(qs)["start"][0]) / 100 + 1
            except:
                pass
        return 1
         
    @staticmethod
    def replace_htmltag(content):
        content = content.replace("<br />", "\n")
        content = content.replace("&nbsp;", " ")
        return content

if __name__ == '__main__':
    bz = DoubanZhibo("http://www.douban.com/group/topic/19157737/", html=True)
    bz = DoubanZhibo("http://www.douban.com/group/topic/21685759/", html=True)
    for x in bz:
        print x["url"]
        for y in x["content"]:
            print y["content"]
            print y["floor"]
