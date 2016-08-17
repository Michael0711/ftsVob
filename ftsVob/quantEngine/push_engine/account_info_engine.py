#coding: utf-8

import json
import time
from .base_engine import BaseEngine
from ..event_engine import *

class AccountInfoEngine(BaseEngine):
    """处理帐户信息引擎将帐户所有信息打包发给策略"""
    EventType = 'account'
    PushInterval = 10
    
    def init(self):
        #暂时作为测试数据
        self.source = {}
        self.register()
        self.query_list = [self.gateway.qryAccount, 
                           self.gateway.qryPosition, 
                           self.gateway.qryOrder, 
                           self.gateway.qryTrade]
        
    def register(self):
        #注册需要的数据推送事件
        self.event_engine.register(EVENT_POSITION, self.get_position)
        self.event_engine.register(EVENT_ACCOUNT, self.get_account)
        self.event_engine.register(EVENT_TRADE, self.get_trade)
        self.event_engine.register(EVENT_ORDER, self.get_order)

    def get_position(self, event):
        self.source['position'] = event.data

    def get_account(self, event):
        self.source['account'] = event.data

    def get_trade(self, event):
        self.source['trade'] = event.data
    
    def get_order(self, event):
        self.source['order'] = event.data

    def fetch_quotation(self):
        for elt in self.query_list:
            elt()
            time.sleep(1)
        return self.source
