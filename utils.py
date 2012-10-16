#coding: utf-8
import os
import hashlib

BASE = os.path.dirname(os.path.abspath(__file__))

def get_path(id):
    """
    生成该小说应该的路径
    """
    hashvalue = hashlib.md5(id).hexdigest()
    return os.path.join(BASE, "novels", hashvalue[:2])

class BaiduWriter(object):
    """
    生成baidu脱水小说的类
    """
    
    def __init__(self, id):
        """
        该类需要做的事情：
            判断html是否存在，如果不存在，新建该文件。
            如果存在，找到上一次的checkpoint，进行追加。
        """
        id = str(id)
        self.path = get_path(id)
        # 路径不存在则创建路径
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
        #生成文件路径
        self.filepath = os.path.join(self.path, "%s.html" % id)
        self.newfile = False
        if not os.path.exists(self.filepath):
            self.newfile = True
            
        #如果是第一次的话就打开文件写入头部信息吧
        if self.newfile:
            self.file = open(self.filepath, "w")
            self.write_header()
        else:
            self.file = open(self.filepath, "r+")
            self.seek_position()
    
    def write_header(self):
        """
        写入html头部信息
        """
        self.file.write("""\
<!doctype html public "-/w3c/dtd html 4.01/en"
"http://www.w3.org/tr/html4/strict.dtd">
<html>
<head>
<meta http-equiv="content-Type" content="text/html; charset=utf-8" />
<style type="text/css">
* {font-size: 14px;margin: 0;padding: 0}
a {text-decoration: none}
a:hover {color: red}
.one_page {
    background-color: #d0d0ff;
    padding: 0 2px;
}
.content_top {
    padding: 0px 4px;
	height: 24px;
	line-height: 24px;
    font-weight: bold;
    font-size: 12px;
    overflow: hidden;
    white-space: nowrap;
}
.content_top a {
    font-size: 12px;
    font-weight: normal;
	text-shadow: 0px 1px 1px white;
}
.content_main {
    padding: 8px 12px;
    border-bottom: 1px dashed #d0d0ff;
    background-color: white;
    line-height: 22px;
}
.floor {
	line-height: 22px;
	display: none;
}
.floor a {
    font-size: 12px;
}
</style>
<script type="text/javascript" src="/static/js/jquery-1.4.3.min.js"></script>
<script type="text/javascript">
	$(function(){
		$('.content_main').hover(
			function(){
				$(this).find('.floor').fadeIn();
			}, 
			function(){
				$(this).find('.floor').hide();
			}
		);
        $.get("/ajax/backup", function(data){
            $(body).append(data);
        })
	});
</script>
</head>
<body>
<div style="width: 950px;margin: 0 auto 10px auto">
        """)
        
    def seek_position(self):
        """
        寻找上一次的写入点
        """
        _total = 0
        for eachline in self.file:
            if "<!--checkpoint-->" in eachline:
                self.file.seek(_total)
                break
            _total += len(eachline)
    
    def write_content(self, page):
        """
        写入正文内容
        """
        self.file.write('''
    <div class="one_page">
    <div class="content_top">
    第 %(page)s 页：<a href="%(url)s" target="_blank">%(url)s</a>
    </div>
        ''' % page)
        for each in page["content"]:
            self.file.write('''
            <div class="content_main">
                <a name="%(floor)s"></a>
                %(content)s
                <span class="floor"><a title="%(floor)s楼" href="#%(floor)s" onclick="top.location.hash='#%(floor)s';alert('设置完成，请添加收藏夹吧！')">[设为书签]</a></span>
            </div>
            ''' % each)
        self.file.write('''</div>''')
        # 内存问题
        self.file.flush()
    
    def write_footer(self):
        """
        写入html尾
        """
        self.file.write("""
    <!--checkpoint-->
</div>
</body>
</html>        
        """)
    
    def close(self):
        """
        关闭文件
        """
        self.write_footer()
        self.file.close()