#coding: utf-8
"""
百度直播贴提取脚本
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
BAIDU_USER_RE = re.compile(r'"name":"(.*?)"')
IS_LZL_RE = re.compile(r'is_lzl:"(.)"')

class BaiduZhibo(object):
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
     
    def __init__(self, main_url, url="", obj_name=None, limit=0, html=False, floor=0):
        self.limit = limit
        self.counter = 0
        self.html = html
        self.floor = floor
        self.nowurl = url or main_url
        self.starturl = url or main_url
        self.is_lzl = False
        
        # 处理页数
#        self.page = 1
#        if PN_RE.search(self.starturl):
#            self.page = int(PN_RE.search(self.starturl).group(1)) / 30 + 1
        
        # 处理obj_name
        self.obj_name = obj_name
        content = reconnecting_urlopen(main_url, retry=100).decode("gbk", "ignore")
        soup = BeautifulSoup(content)
        log.info("content %s %s %s" % (len(content), type(content), content[:100]))

        # 查看是不是新版本，楼中楼(2011.09.26)
        is_lzl_re = IS_LZL_RE.search(content)
        if is_lzl_re:
            self.is_lzl = bool(int(is_lzl_re.group(1)))

        if not self.obj_name:
            # 获得楼主昵称
#            self.obj_name = self.get_username(soup.find("div", {"class": "post"}))
            self.obj_name = self.get_username(soup.find("div", {"class": "p_post"}))
    
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
        posts = soup.findAll("div", {"class": "l_post"})
        for post in posts:
            username = self.get_username(post)
            if username == self.obj_name:
                floor, cc = self.parse_post(post)
                 
                if not self.html:
                    cc = self.replace_htmltag(cc)
                    
                # 判断楼层数
                if floor > self.floor:
                    result["content"].append({
                        "floor": floor,
                        "content": _br(cc),
                    })
        self.nowurl = self.get_nexturl(soup)
        self.counter += 1

        try:
            page = soup.find("li", {"class": "l_pager"})\
                       .find("span", {"class": "tP"})\
                       .renderContents()
        except:
            page = 1
        result["page"] = page
        return result
         
    def __iter__(self):
        return self
     
    def get_username(self, post):
        """
        获得用户姓名
        """
        obj = BAIDU_USER_RE.search(str(post))
        if obj:
            return obj.group(1)
        return ""
     
    def parse_post(self, post):
        """
        返回楼数和内容
        """
        # 兼容两版模式
        if self.is_lzl:
            _content = post.find('div', {"class": "p_content"})
        else:
            _content = post.find('td', {"class": "d_content"})
                         
        floor = _content.find('p', {"class": "d_floor"}).renderContents()
        floor = DIGIT_RE.search(floor).group()
#        cc = _content.find('cc').renderContents()
        cc = _content.find('p', id=CONTENTP_RE).renderContents()
        return int(floor), cc
 
    def get_nexturl(self, soup):
        """
        从页面获得下一页url
        """
        next = soup.find(text=u"下一页")
        if next:
            return urlparse.urljoin(self.starturl, next.parent.get("href")).encode("utf-8")
        return None
         
    @staticmethod
    def replace_htmltag(content):
        content = content.replace("<br />", "\n")
        content = content.replace("&nbsp;", " ")
        return content

if __name__ == '__main__':
#    bz = BaiduZhibo("http://tieba.baidu.com/p/1177153446", "http://tieba.baidu.com/p/1177153446", html=True)
    bz = BaiduZhibo("http://tieba.baidu.com/p/1162457290", "http://tieba.baidu.com/p/1162457290", html=True)
    for x in bz:
        print x["page"], x["url"]
        for y in x["content"]:
            print y["content"]
