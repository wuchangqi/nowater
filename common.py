#coding: utf-8
import re
import urllib
import urllib2

from settings import NOTIFY_URL

BR_RE = re.compile(r"([\s　]*<br[^>]*>){2,}", re.I)
IMG_RE = re.compile(r'''(<img.*?src=(['"]))(.*?)(\2.*?>)''', re.I)
ORIGINAL_RE = re.compile(r'''\soriginal=(['"])(.*?)\1''', re.I)
OBJ_IMG_RE = re.compile(r'''
    http://hiphotos.baidu.com |
    http://imgsrc.baidu.com |
    http://img\d*.tianya.cn |
    http://img\d*.laibafile.cn
''', re.VERBOSE)

def remove_br(content):
    """
    去掉多余的换行
    同时处理图片的反盗链
    """
    content = BR_RE.sub(r"<br /><br />", content)
    if IMG_RE.search(content):
        content = IMG_RE.sub(trans_src, content)
    return content

def trans_src(obj):
    """
    改变img的src
    """
    pre = obj.group(1)
    src = obj.group(3)
    aft = obj.group(4)
    _obj = ORIGINAL_RE.search(obj.group())
    if _obj:
        src = _obj.group(2)
        pre = '<img src="'
        aft = '" />'

    if OBJ_IMG_RE.search(src):
        src = r"/get_outside_image/%s" % src.split(r"/", 2)[-1]
    return "".join((pre, src, aft))

TAG_RE = re.compile(ur"<[^>]+>|\s|　|&nbsp;")
def strip_tag(content):
    """
    忽略标签
    """
    return TAG_RE.sub("", content)

def notify_page(id, page):
    """
    通知原始页面抓取完成
    """
    try:
        urllib2.urlopen(NOTIFY_URL, urllib.urlencode({"id": id,"page": page}))
    except:
        pass

def reconnecting_urlopen(*args, **kwargs):
    """
    会重复尝试的urlopen，默认尝试5次
    """
    retry_count = kwargs.setdefault("retry", 5)
    try:
        _kwargs = kwargs.copy()
        _kwargs.pop("retry")
        content = urllib2.urlopen(*args, **_kwargs).read()
        return content
    except Exception, e:
        if retry_count:
            kwargs["retry"] -= 1
            return reconnecting_urlopen(*args, **kwargs)
        else:
            raise e

