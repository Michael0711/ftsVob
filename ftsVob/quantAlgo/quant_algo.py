#coding: utf-8
import datetime
import time
import threadpool
import json

from threading import Thread
from threadpool import ThreadPool 
from ..quantGateway.quant_constant import *
from ..quantGateway.quant_gateway import *
from ..logHandler import DefaultLogHandler
from ..errorHandler import ErrorHandler

"""
GateWay的上层封装
这里实现了一些算法交易的类
Engine层和Strategy层只和算法交易层交互
"""

class AlgoTrade(object):
    """算法交易接口"""
    def __init__(self, gateWay, eventEngine, thread_pool_size=30):
        """Constructor"""
        self.gateway = gateWay
        self.eventengine = eventEngine
        self.log = self.log_handler()

        #错误处理的log可以选择gateway的log，默认选择Algo的log系统
        self.err = ErrorHandler(log=self.log)

        #处理多合约这里设计为一个二级字典
        #{'symbol':{'orderID': orderObj}}
        self.orderinfo = {}
        
        #Req<-->Resp的反查数组
        #{'requestID':orderID}
        self.request = {}
        self.register()

        #建立线程池用来处理小单，默认线程池大小为30
        self.pool = threadpool.ThreadPool(thread_pool_size)
        
        #返回给客户端数据(在网络交易模式下)
        self.ret_client_data = {}

    def twap(self, size, reqobj, price=0, sinterval=1, mwtime=60, wttime=2):
        """TWAP对外接口
        @sinterval: 发单间隔时间，小单间隔
        @mwtime: 最长等待时间，主线程的最长等待时间
        @wttime: 等待成交时间，发单线程等待成交时间
        """
        self.twap_thread = Thread(target=self.twap_callback, args=(size, reqobj, price, sinterval, mwtime, wttime))
        self.twap_thread.start()

    def vwap(self, size, reqobj, price=0, sinterval=1, mwtime=60, wttime=2):
        """VWAP对外接口
        @sinterval: 发单间隔时间，小单间隔
        @mwtime: 最长等待时间，主线程的最长等待时间
        @wttime: 等待成交时间，发单线程等待成交时间
        """
        self.vwap_thread = Thread(target=self.vwap_callback, args=(size, reqobj, price, sinterval, mwtime, wttime))
        self.vwap_thread.start()

    def send_child_order(self, reqobj, wttime): 
        par = list()
        par.append(([reqobj,wttime],{}))
        requests = threadpool.makeRequests(self.process_child, par)
        [self.pool.putRequest(req) for req in requests]
        
    def process_cancel(self, reqobj, wttime, order_ref):
        """处理撤单逻辑
        """
        max_cancel_cnt = 3
        while True:
            try:
                of = self.request[str(order_ref)]
                if of.status == STATUS_NOTTRADED or of.status == STATUS_PARTTRADED: 
                    cancel_obj = VtCancelOrderReq()
                    cancel_obj.symbol = of.symbol
                    cancel_obj.exchange = of.exchange
                    cancel_obj.orderID = of.orderID
                    cancel_obj.frontID = of.frontID
                    cancel_obj.sessionID = of.sessionID
                    self.gateway.cancelOrder(cancel_obj)
                if of.status == STATUS_CANCELLED:
                    #计算剩余单数
                    remain_v += of.remainVolume
                    self.log.info('----------------cancelled-----------')
                    self.log.info(remain_v)
                    #启动发单子进程 
                    if remain_v > 0:
                        reqobj.volume = remain_v
                        self.send_child_order(reqobj, wttime)
                        break
            except KeyError: 
                self.log.error(u'未获取合约交易信息尝试三次以后子线程终止')
            finally:
                max_cancel_cnt -= 1
                if max_cancel_cnt == 0:
                    break


    def process_child(self, reqobj, wttime):
        """发单子线程
        @reqobj: 发单请求
        @wttime: 等待成交时间
        """
        remain_v = 0
        reqobj.price = round(self.gateway.tickdata[reqobj.symbol].tolist()[-1].bidPrice1, 1)
        order_ref = self.gateway.sendOrder(reqobj)
        self.log.info('------------------------sendinfo-------------------')
        self.log.info(json.dumps(reqobj.__dict__))
        time.sleep(wttime)
        self.process_cancel(reqobj, wttime, order_ref)  
        return
             
    def twap_callback(self, size, reqobj, price, sinterval, mwtime, wttime):
        """Time Weighted Average Price
        每次以线程模式调用
        @size: 小单规模
        @reqobj: 发单请求
        @price: 下单价格，默认为0表示按照bid1下单
        其余参数和对外接口保持一致
        """
        volume = reqobj.volume
        self.volume = volume
        if volume % size > 0:
            count = volume // size + 1
        else:
            count = volume // size

        for i in range(count):
            if i == count - 1:
                reqobj.volume = (volume - i*size) 
                self.send_child_order(reqobj, wttime)
            else:
                reqobj.volume = size
                self.send_child_order(reqobj, wttime)
            time.sleep(sinterval)
        self.pool.wait()
        #最大等待时间
        time.sleep(mwtime - count * sinterval)
        #剩余单数以对手价格下单
        if self.volume > 0:
            rb_data = self.gateway.tickdata[reqobj.symbol].tolist()[-1]
            price = round(rb_data.askPrice1, 1)
            reqobj.price = price
            reqobj.volume = self.volume
            self.gateway.sendOrder(reqobj)
        return
        
    def get_order_info_callback(self, event):
        #建立orderinfo二级字典
        if event.data.symbol in self.orderinfo: 
            self.orderinfo[event.data.symbol][event.data.orderID] = event.data
        else:
            self.orderinfo[event.data.symbol] = dict()
            self.orderinfo[event.data.symbol][event.data.orderID] = event.data
         
        #建立request反查字典
        self.request[event.data.orderID] = event.data

    def get_trade_info_callback(self, event):
        tradeinfo = event.data
        self.orderinfo[tradeinfo.symbol][tradeinfo.orderID].status = STATUS_ALLTRADED

        #收到成交回报更新总单数
        self.volume -= tradeinfo.volume
        self.log.info('----------------------------success----------------')
        self.log.info(self.volume)
        if 'tradeinfo' not in self.ret_client_data:
            self.ret_client_data['tradeinfo'] = list()
            self.ret_client_data['tradeinfo'].append(tradeinfo.__dict__)
        else:
            self.ret_client_data['tradeinfo'].append(tradeinfo.__dict__)

    def register(self):
        self.eventengine.register(EVENT_TRADE, self.get_trade_info_callback)
        self.eventengine.register(EVENT_ORDER, self.get_order_info_callback)
        self.eventengine.register(EVENT_ERROR, self.err.process_error)

    def log_handler(self):    
        return DefaultLogHandler(name=__name__)

    def vwap_callback(self, size, reqobj, price, sinterval, mwtime, wttime):
        pass
        
