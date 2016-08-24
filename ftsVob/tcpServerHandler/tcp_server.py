#coding: utf-8
import time
import json
import socket,threading,asyncore

from ..logHandler import DefaultLogHandler
from ..quantEngine.event_engine import *

RECVDATASIZE = 1024

class FtsTcpServer(object):
    
    def __init__(self, cfg, gateway, eventengine):
        """
        FtsTcpServer的构造函数负责初始化一些服务器属性
        @cfg: 字典型配置文件
        """
        f = file(cfg)
        setting = json.load(f)
        self.port = int(setting['port'])
        self.name = setting['name']
        self.rdtmout = setting['readtimeout']
        self.wrtmout = setting['writetimeout']
        self.conntype = setting['conntype']
        self.threadnum = setting['threadnum']
        self.queuesize = setting['queuesize']

        self.net = FtsServerNetLib(self)
        self.gateway = gateway
        self.eventengine = eventengine
        self.callback = None
        self.sendlist = {}

    def setCallback(self, cb):
        self.callback = cb
        
    def start(self):
        self.bt = threading.Thread(target = self.net.start)
        self.bt.start()

        #等待线程启动
        time.sleep(0.001)

    def stop(self):
        self.net.stop()
        #等待端口被重用
        time.sleep(0.01)

    def clear(self):
        self.callback = None

class FtsServerNetLib(asyncore.dispatcher):
    """
    异步服务器
    """

    def __init__(self, fts_tcp_server):
        """
        初始化函数
        @fts_tcp_server: 传入fts_tcp_server句柄
        """
        asyncore.dispatcher.__init__(self)
        self.server = fts_tcp_server
        self.is_running = False
        self.conncond = threading.Condition()
        self.twork = []
        self.connections = []
        self.__lock = threading.Lock()
        self.log = DefaultLogHandler(name=__name__)
        self.connmap = {}

    def start(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("", self.server.port))
        self.listen(self.server.queuesize)
        self.twork = []
        self.connections = []
        self.register()

        self.is_running = True
        for i in range(self.server.threadnum):
            self.twork.append(threading.Thread(target = self.thread_work))
        for i in range(self.server.threadnum):
            self.twork[i].start()
        asyncore.loop(0.01)

    def stop(self):
        if self.is_running == True:
            self.is_running = False
            for i in range(self.server.threadnum):
                self.twork[i].join()
            self.del_channel()
            self.close()

    def register(self):
        self.server.eventengine.register(EVENT_CLIENT, self.send_msg_by_clientid)

    def thread_work(self):
        while self.is_running:
            conn = self.__get_conn()
            if not conn: break

            try:
                self.__lock.acquire()
                sock,addr = conn
                
                self.log.info(conn)
                #接收数据
                #设置读取超时时间
                sock.settimeout(self.server.rdtmout)
                recvRaw = sock.recv(RECVDATASIZE)
                self.log.info(recvRaw)
                self.server.sendlist = json.loads(recvRaw)

                #建立客户端映射
                self.connmap[self.server.sendlist['clientid']] = conn
                

                #调用服务器的回调函数，这里可以设置TWAP函数
                if self.server.callback:
                    rspdata = self.server.callback(self.server)
                else:
                    self.__lock.release()
                    raise RuntimeError,'callbackfunc must set first'

                #返回客户端Resp数据，这里可以是TWAP的返回值
                sock.settimeout(self.server.wrtmout)
                #返回数据用Json格式，需要转成字符
                sendRawData = ''
                sent = 0
                while sent < len(sendRawData):
                    sent += sock.send(sendRawData)

                if self.server.conntype:
                    self.log.info('euxyacg conntype:%d' % self.server.conntype)
                    self.__put_conn(conn)
                else:
                    self.log.info('euxyacg conntype:%d' % self.server.conntype)
                    #conn[0].close()
                self.__lock.release()
            except socket.error, why:
                self.__lock.release()
                self.log.warning('socket[%d] %s', conn[0].filno(), why)
                conn[0].close()
                

    def handle_accept(self):
        try:
            conn = self.accept()
        except socket.error:
            self.log.warning("server accept() threw an exception")
            return
        except TypeError:
            self.log.warning("stub accept() threw EWOULDBLOCK")
            return
        if conn: self.__put_conn(conn)

    def __get_conn(self):
        self.conncond.acquire()
        while len(self.connections) == 0 and self.is_running:
            self.conncond.wait(1)
        if not self.is_running:
            self.conncond.release()
            return None
        conn = self.connections.pop(0)
        self.conncond.release()
        return conn

    def __put_conn(self, conn):
        self.conncond.acquire()
        self.connections.append(conn)
        self.conncond.notify()
        self.conncond.release()

    def send_msg_by_clientid(self, event):
        """
        事件回调函数发送回报消息给特定客户端
        """
        data = event.data
        self.log.info(self.connmap[data.keys()[0]])
        sock,addr = self.connmap[data.keys()[0]]
        send = 0
        msg = data.values()[0]
        self.log.info('euxyacg')
        self.log.info(msg)
        while send < len(msg):
            send += sock.send(msg)
        

def test_call_back(ftsserver):
    print('euxyacg')
    return json.dumps({'euxyacg':2})
    
def main():
    fts_server = FtsTcpServer({'name':'test', 'port':12345})
    fts_server.setCallback(test_call_back)
    fts_server.start()
    try:
        while True:
           time.sleep(0.5)
    except KeyboardInterrupt:
        fts_server.stop()

if __name__ == '__main__':
    main()
