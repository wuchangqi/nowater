#coding: utf-8
from twisted.web import resource, server
from twisted.internet import task
from twisted.internet.threads import deferToThread

import time

from main import do_work, ready_work
from basedb import BaseDB

class MsgBox(object):
    """
    处理所有消息的类
    
    每一个连接对象包括:
        msg: 消息内容，也就是页数
        last_time: 上次连上来的时间戳
        request: request对象
    """
    def __init__(self):
        self.box = {}
    
    def connection_made(self, id, client_id, request):
        """
        用户连接进来
        """
        if id not in self.box:
            return "not found"
        l_box = self.box[id]
        client = l_box.setdefault(client_id, Client())
        client.login(request)
        
        # 如果还有信息,则返回给用户
        if client.msg:
            client.return_msg()
            return

        if not l_box.get("status", True):
            return "end"

        return client
            
    def new_msg(self, id, page):
        """
        有新页来了
        """
        l_box = self.box.setdefault(id, {})
        for c in l_box.values():
            if not isinstance(c, bool):
                c.msg.append(page)
                c.return_msg()
        if page == "end":
            l_box["status"] = False
        else:
            l_box["status"] = True
            
class Client(object):
    """
    用户类
    """
    EXPIRED_TIME = 30
    
    def __init__(self):
        """
        初始化用户类
        """
        self.msg = []
        self.status = True
        self.last_time = None
        self.request = None
        
    def __str__(self):
        return "%s;%s;%s" % (self.request, self.msg, self.last_time)
        
    def login(self, request):
        """
        登入
        """
        if self.status and self.request is not None:
            self.request.write("end")
            self.request.finish()
        self.request = request
        self.check_expired()
        self.last_time = time.time()
        self.status = True
        
    def return_msg(self):
        """
        返回信息
        """
        if self.request is None:
            return
        self.request.write(",".join(self.msg))
        self.msg = []
        self.request.finish()
        self.request = None
        self.status = False
        
    def check_expired(self):
        """
        查看是否过期，如果超过过期时间，则清空所有msg
        """
        if self.last_time and (time.time() - self.last_time) > self.EXPIRED_TIME:
            self.msg = []

mb = MsgBox()

def clean_clients():
    """
    清除一个小时内没有登录过的clients
    """
    for clients in mb.box.values():
        clients = dict([(x, y) for (x, y) in clients.items() if x == "status" or (y.last_time and (time.time() - y.last_time) < 3600)])

class Progress(resource.Resource):
    """
    返回进度
    """
    
    def render_GET(self, request):
        id = request.args.get("id", [""])[0]
        client_id = request.args.get("client_id", [""])[0]
        
        client = mb.connection_made(id, client_id, request)
        if client is None:
            return server.NOT_DONE_YET
        elif isinstance(client, str):
            return client
        else:
            request.notifyFinish().addErrback(self.disconnect, client)
            return server.NOT_DONE_YET
    
    def disconnect(self, ret, client):
        """
        客户端断开连接
        """
        client.request = None
        client.status = False
    
    def render_POST(self, request):
        """
        通知某小说更新到了某一页
        page:
            start 开始
            r_12 表示初始页面的12页
            o_12 表示小说页面的12页
            end 结束
        """
        id = request.args.get("id", [""])[0]
        page = request.args.get("page", [""])[0]
        print request.args
        mb.new_msg(id, page)
        return "ok"
        
    
class StartWork(resource.Resource):
    """
    开始抓取
    """
    def render_GET(self, request):
        # 传入一个id，直接开始该id的抓取工作
        id = request.args.get("id", [""])[0]
        if id.isdigit():
            db = BaseDB()
            info = db.get_novel_by_id(id)
            if info:
                # 准备工作
                if ready_work(info, db):
                    mb.new_msg(id, 'start')
                    deferToThread(do_work, info, db).addErrback(self.get_error, id, db)
        return "ok"

    def get_error(self, error, id, db):
        print error
        db.modify_status(id, 4)
        mb.new_msg(id, 'end')

root = resource.Resource()
root.putChild("", type("Index", (resource.Resource, object), {
    "render_GET": (lambda *args: "ready")
})())
root.putChild("progress", Progress())
root.putChild("start_work", StartWork())

task.LoopingCall(clean_clients).start(60, now=False)

from twisted.application import service, internet
from twisted.internet import reactor
reactor.suggestThreadPoolSize(100)

site = server.Site(root)
application = service.Application("nowater_progress")
s = internet.TCPServer(9000, site)
s.setServiceParent(application)
