#coding: utf-8
import os
import re
from BeautifulSoup import BeautifulSoup

BR_RE = re.compile(r"(<br[^>]*>\s*){2,}", re.I)

for directory, subdirs, files in os.walk("../novels"):
    for file in files:
        if file.endswith(".html"):
            content = open(os.path.join(directory, file), "r+").read()
            obj_content = ""
            soup = BeautifulSoup(content)
            for x in soup.contents:
                if hasattr(x, "get"):
                    [t.extract() for t in x.findAll("span", {"class": "fromwap"})]
                    _content = BR_RE.sub(r"<br /><br />", str(x))
                    obj_content += _content
                    open(os.path.join(directory, file), "w").write(obj_content)
