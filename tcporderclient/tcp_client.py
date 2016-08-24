#coding: utf-8
import time
import json
import socket,threading

class FtsTcpClient(object):
    
    def __init__(self, cfg):
        """ 
        FtsTcpServer的构造函数负责初始化一些客户端属性
        @cfg: 字典型配置文件
        """
        f = file(cfg)
        setting = json.load(f)
        self.port = int(setting['port'])
        self.ip = setting['ip']
        self.name = setting['name']
        self.rdtmout = setting['readtimeout']
        self.wrtmout = setting['writetimeout']
        self.cntmout = setting['connecttimeout']
        self.conntype = setting['conntype']
        self.net = FtsClientNetLib(self)

    def doRequest(self):
        self.net.invite(self.orderobj)

    def setRequest(self, path):
        f = file(path)
        self.orderobj = json.load(f)

class FtsClientNetLib():
    
    def __init__(self, driver):
        self.driver = driver
        self.sockets = []
        self.socket_num = 0
        self.sockcond = threading.Condition()

    def __connect(self):
        try:
            sock = socket.create_connection((self.driver.ip, self.driver.port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error, why:
            print("driver connect error (%s), ip(%s), port(%d)", why, self.driver.ip , self.driver.port)
            return None
        return sock

    def __get_socket(self):
        self.sockcond.acquire()
        if len(self.sockets) == 0:
            sock = self.__connect()
            if sock: self.socket_num += 1
        else:
            sock = self.sockets.pop(0)
        self.sockcond.release()
        return sock

    def __put_socket(self, sock):
        self.sockcond.acquire()
        if not sock:
            self.socket_num -= 1
        elif self.driver.conntype:
            self.sockets.append(sock)
        else:
            sock.close()
            self.socket_num -= 1
        self.sockcond.notify()
        self.sockcond.release()

    def invite(self, send_order):
        #获取端口
        sock = self.__get_socket()
        if not sock:
            print("driver connect failed")
            return
        try:
            #发送请求
            reqRawData = json.dumps(send_order)
            sent = 0
            while sent < len(reqRawData):
                sent += sock.send(reqRawData)

            #接收回报
            recvRaw = sock.recv(1024)
            print(recvRaw)
            self.__put_socket(sock)

        except socket.error, why:
            print("socket error (%s)", why)
            sock.close()
            self.__put_socket(None)

def main():
    driver = FtsTcpClient('order_client.json')
    driver.setRequest('order_list.json')
    driver.doRequest()
    while True:
        time.sleep(0.5)


if __name__ == '__main__':
    main()
