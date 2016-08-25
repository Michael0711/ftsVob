#coding: utf-8
import MySQLdb
import ConfigParser
import json
import codecs

"""
fts数据库支持类关系型数据库mysql
用于记录成交记录，录入历史数据等
"""

class MysqlIo(object):
    """Mysql操作类"""
    def __init__(self, conf):
        self.cf = ConfigParser.ConfigParser()
        self.cf.readfp(codecs.open(conf, "r", "utf-8-sig"))
        self.name = "DB"
        self.db_host     = self.cf.get(self.name, "host")
        self.db_user     = self.cf.get(self.name, "user")
        self.db_passwd   = self.cf.get(self.name, "passwd")
        self.db_name     = self.cf.get(self.name, "name")
        self.db_port     = self.cf.get(self.name, "port")
        self.db_sock     = self.cf.get(self.name, "sock")

    def execute_sql(self,sql):
        db = MySQLdb.connect(user=self.db_user,\
                             host=self.db_host,\
                             passwd=self.db_passwd,\
                             db=self.db_name,\
                             unix_socket=self.db_sock,\
                             port=int(self.db_port))

        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        cursor.close()
        db.close()
