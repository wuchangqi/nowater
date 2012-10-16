#coding: utf-8
import os
import re

img_re = re.compile(r'''(<img.*?src=(['"]))(.*?)(\2.*?>)''', re.I)
OBJ_IMG_RE = re.compile(r"(http://hiphotos.baidu.com|http://imgsrc.baidu.com|http://img\d*.tianya.cn)")

def trans_src(obj):
    """
    改变img的src
    """
    pre = obj.group(1)
    aft = obj.group(4)
    src = obj.group(3)
    if OBJ_IMG_RE.search(src):
        return r"%s/get_outside_image/%s%s" % (pre, src.split(r"/", 2)[-1], aft)
    return obj.group()

for dir, subdirs, files in os.walk("../novels"):
    for file in files:
        if file.endswith(".html"):
            content = open(os.path.join(dir, file), "r+").read()
            if img_re.search(content):
                content = img_re.sub(trans_src, content)
                open(os.path.join(dir, file), "w").write(content)
