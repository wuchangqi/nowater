#coding: utf-8
import os
import re
from BeautifulSoup import BeautifulSoup

img_re = re.compile(r'''(<img.*?src=(['"]))(.*?)(\2.*?>)''', re.I)

def trans_contenttop(content):

    return None

for directory, subdirs, files in os.walk("../novels"):
    for file in files:
        if file.endswith(".html"):
            content = open(os.path.join(directory, file), "r+").read()
            obj_content = ""
            soup = BeautifulSoup(content)
            for x in soup.contents:
                if hasattr(x, "get") and x.get("class") == 'content_top':
                    temp = x.next.string
                    x.next.replaceWith(u"原帖" + temp.strip())
                    x.a.next.replaceWith("查看该页内容")
                obj_content += str(x)
                open(os.path.join(directory, file), "w").write(obj_content)
