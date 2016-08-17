#coding: utf-8
from ftsVob.quantGateway.quant_constant import *
from ftsVob.quantGateway.quant_gateway import  *

from ftsVob import  StrategyTemplate
from ftsVob import  DefaultLogHandler
from ftsVob import  AlgoTrade

import os
import time
import datetime

SPLITLINE='----------------------------------------------------'

class Strategy(StrategyTemplate):
    name = 'Cta strategy'

    def strategy(self, event):
        self.log.info(u'Cta 策略触发')
        self.log.info(event.data)
        self.log.info('\n')

    def log_handler(self):
        return DefaultLogHandler(name=__name__, log_type='file')
    
    def run(self, event):
        self.log.info(event.data)
        if self.is_whole_info(event):
            self.write2file(event)
            self.kill_process()
        else:
            self.log.info('Pls waiting more time')

    def kill_process(self):
        os.system('sh daemonvt.sh stop')

    def is_whole_info(self, event):
        data = event.data
        if ('account' in data and
            'position' in data and
            'order' in data and
            'trade' in data):
            return True
        else:
            return False
    
    def write2file(self, event):
        dnow = datetime.datetime.now()
        dstr = dnow.strftime('%Y%m%d')
        filename = self.gateway.tdApi.userID + '.' + dstr  
        fp = open(filename, 'w')
        fp.write(SPLITLINE+'\n')
        data = event.data['account']
        fp.write('ACCOUNT:\n')
        fp.write('prebalance: ' + str(data.preBalance) + '\n')
        fp.write('available: ' + str(data.available) + '\n')
        fp.write('commission: ' + str(data.commission) + '\n')
        fp.write('margin: ' + str(data.margin) + '\n')
        fp.write('closeprofit: ' + str(data.closeProfit) + '\n')
        fp.write('positionProfit: ' + str(data.positionProfit) + '\n')
        fp.write('balance: ' + str(data.balance) + '\n')
        fp.write(SPLITLINE+'\n')

        fp.write('POSITION:\n')
        data = event.data['position']
        ret_table = self.list2readable_table4pos(data)
        self.write_content(fp, ret_table)
        fp.write(SPLITLINE+'\n')

        fp.write('ORDER:\n')
        data = event.data['order']
        ret_table = self.list2readable_table4order(data)
        self.write_content(fp, ret_table)
        fp.write(SPLITLINE+'\n')

        fp.write('TRADE:\n')
        data = event.data['trade']
        ret_table = self.list2readable_table4trade(data)
        self.write_content(fp, ret_table)
        fp.write(SPLITLINE+'\n')
        fp.close()

    def list2readable_table4pos(self, data):
        ret = dict()
        for elt in data:
            self.add_element(ret, 'symbol', elt.symbol)
            self.add_element(ret, 'direction', elt.direction)
            self.add_element(ret, 'position', elt.position)
            self.add_element(ret, 'price', elt.price)
            self.add_element(ret, 'frozen', elt.frozen)
        return ret

    def list2readable_table4order(self, data):
        ret = dict()
        for elt in data:
            self.add_element(ret, 'symbol', elt.symbol)
            self.add_element(ret, 'orderID', elt.orderID)
            self.add_element(ret, 'direction', elt.direction)
            self.add_element(ret, 'offset', elt.offset)
            self.add_element(ret, 'price', elt.price)
            self.add_element(ret, 'totalVolume', elt.totalVolume)
            self.add_element(ret, 'tradedVolume', elt.tradedVolume)
            self.add_element(ret, 'status', elt.status)
            self.add_element(ret, 'orderTime', elt.orderTime)
            self.add_element(ret, 'cancelTime', elt.cancelTime)
        return ret
        
    def list2readable_table4trade(self, data):
        ret = dict()
        for elt in data:
            self.add_element(ret, 'symbol', elt.symbol)
            self.add_element(ret, 'tradeID', elt.tradeID)
            self.add_element(ret, 'orderID', elt.orderID)
            self.add_element(ret, 'direction', elt.direction)
            self.add_element(ret, 'offset', elt.offset)
            self.add_element(ret, 'price', elt.price)
            self.add_element(ret, 'volume', elt.volume)
            self.add_element(ret, 'tradeTime', elt.tradeTime)
        return ret

    def write_content(self, fp, ret):
        itemlist = sorted(ret.keys())
        for ki in itemlist:
            fp.write(ki+'\t\t')
        fp.write('\n')
        for ki in range(len(ret[itemlist[0]])):
            for kj in itemlist:
                fp.write(str(ret[kj][ki]) + '\t\t')
            fp.write('\n')
        
    def add_element(self, d, key, v):
        if key not in d:
            d[key] = list()
            d[key].append(v)
        else:
            d[key].append(v)
        return d
            
