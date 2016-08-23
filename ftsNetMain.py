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
        #Algo相关参数提取
        size = ftsserver.sendlist[elt]['size']
        t1 = ftsserver.sendlist[elt]['sinterval']
        t2 = ftsserver.sendlist[elt]['mwtime']
        t3 = ftsserver.sendlist[elt]['wttime']
        #转换下单对象
        orderreq = convert_order2reqobj(ftsserver.sendlist[elt])
        orderreq.symbol = elt
        algo.twap(size, orderreq, sinterval=t1, mwtime=t2, wttime=t3)

def convert_order2reqobj(elt):
    """客户端发过来的数据需要转成真实的下单""" 
    ret_order_obj = ftsVob.VtOrderReq()
    if elt['priceType'] == 'PRICETYPE_FOK':
        ret_order.priceType = PRICETYPE_FOK
    elif elt['priceType'] == 'PRICETYPE_FAK':
        ret_order.priceType = PRICETYPE_FAK
    elif elt['priceType'] == 'PRICETYPE_MARKETPRICE':
        ret_order.priceType = PRICETYPE_MARKETPRICE
    else:
        ret_order.priceType = PRICETYPE_LIMITPRICE
    
    if elt['direction'] == 'DIRECTION_LONG':
        ret_order.direction = DIRECTION_LONG
    else:
        ret_order.direction = DIRECTION_SHORT

    if elt['offset'] == 'OFFSET_OPEN':
        ret_order.offset = OFFSET_OPEN
    else:
        ret_order.offset = OFFSET_CLOSE

    ret_order_obj.volume = elt['volume']
    return ret_order_obj

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
