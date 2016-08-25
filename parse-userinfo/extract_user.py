#coding: utf-8
"""
用于反序列化用户信息
提供API可以灵活查询
帐户，持仓，下单，交易信息
"""
import os
import sys
import json

class ParseApi(object):

    def __init__(self, path):
        with open(path) as f:
            line = f.readline().strip()
        self.rawobj = json.loads(line)

    def get_position(self):
        return self.rawobj['position']

    def get_account(self):
        return self.rawobj['account']

    def get_order(self):
        return self.rawobj['order']

    def get_trade(self):
        return self.rawobj['trade']

"""
def main():
    pa = ParseApi('063692.20160818.serial')
    print(pa.get_position())
    print(pa.get_account())
    print(pa.get_order())
    print(pa.get_trade())

    
if __name__ == '__main__':
    main()
"""
