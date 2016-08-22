#coding: utf-8

import os
import ftsVob

def send_order_call_back(ftsserver):
    """下单的回调函数"""
    #根据下单合约首先订阅
    for elt in ftsserver.sendlist:
        ftsserver.gateway.subscribe(elt) 

    #调用Algo下单
    algo = ftsVob.AlgoTrade(ftsserver.gateway, ftsserver.eventengine)
    for elt in ftsserver.sendlist:
        orderreq = ftsVob.VtOrderReq()
        orderreq.symbol = elt
        orderreq.volume = ftsserver.sendlist[elt]['volume']
        orderreq.priceType = ftsserver.sendlist[elt]['priceType']
        orderreq.direction = ftsserver.sendlist[elt]['direction']
        orderreq.offset = ftsserver.sendlist[elt]['offset']
        algo.twap(ftsserver.sendlist[elt]['size'], 
                  orderreq, 
                  sinterval=ftsserver.sendlist[elt]['sinterval'],
                  mwtime=ftsserver.sendlist[elt]['mwtime'],
                  wttime=ftsserver.sendlist[elt]['wttime'])
    
def main():
    """期货下单模块"""
    """调用FtsServer模块网络交互下单"""
    
    #配置文件
    serverconfig = 'order_server.json'
    gatewayname = 'CTP'
    gatewayconfig = 'ctp.json'
    event_engine = ftsVob.quantEngine.EventEngine()
    gateway = ftsVob.quantGateway.Use(gatewayname, gatewayConf=gatewayconfig, eventEngine=event_engine, log=ftsVob.logHandler.DefaultLogHandler(name=__name__)) 
    gateway.connect()
    event_engine.start()
    
    #输出程序pid
    with open('fts_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    s = ftsVob.FtsTcpServer(serverconfig, gateway, event_engine)
    s.setCallback(send_order_call_back)
    #启动服务器监听端口
    s.start()

if __name__ == '__main__':
    main()
