#coding: utf-8
import time
import json
import socket,threading,asyncore

#from ..logHandler import DefaultLogHandler

RECVDATASIZE = 1024

class FtsTcpServer(object):
    
    def __init__(self, cfg):
        """
        FtsTcpServer的构造函数负责初始化一些服务器属性
        @cfg: 字典型配置文件
        """
        self.port = int(cfg.get("port",23456))
        self.name = cfg.get("name","base_stub")
        self.rdtmout = cfg.get("readtimeout",0.2)
        self.wrtmout = cfg.get("writetimeout",0.2)
        self.conntype = cfg.get("conntype",0)
        self.threadnum = cfg.get("threadnum",1)
        self.queuesize = cfg.get("queuesize",2)

        self.net = FtsServerNetLib(self)
        self.callback = None

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
        #self.log = DefaultLogHandler(name=__name__)

    def start(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("", self.server.port))
        self.listen(self.server.queuesize)
        self.twork = []
        self.connections = []

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

    def thread_work(self):
        while self.is_running:
            conn = self.__get_conn()
            if not conn: break

            try:
                self.__lock.acquire()
                sock,addr = conn

                #接收数据
                #设置读取超时时间
                sock.settimeout(self.server.rdtmout)
                recvRaw = sock.recv(RECVDATASIZE)
                print(recvRaw)

                #调用服务器的回调函数，这里可以设置TWAP函数
                if self.server.callback:
                    rspdata = self.server.callback(self.server)
                else:
                    self.__lock.release()
                    raise RuntimeError,'callbackfunc must set first'

                #返回客户端Resp数据，这里可以是TWAP的返回值
                sock.settimeout(self.server.wrtmout)
                sendRawData = rspdata
                sent = 0
                while sent < len(sendRawData):
                    sent += sock.send(sendRawData)

                if self.server.conntype:
                    self.__put_conn(conn)
                else:
                    conn[0].close()
                self.__lock.release()
            except socket.error, why:
                self.__lock.release()
                #self.log.warning('socket[%d] %s', conn[0].filno(), why)
                print('socket[%d] %s', conn[0].filno(), why)
                conn[0].close()
                

    def handle_accept(self):
        try:
            conn = self.accept()
        except socket.error:
            #self.log.warning("server accept() threw an exception")
            print("server accept() threw an exception")
            return
        except TypeError:
            #self.log.warning("stub accept() threw EWOULDBLOCK")
            print("stub accept() threw EWOULDBLOCK")
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
