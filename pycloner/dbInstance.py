import sqlite3

class dbInstance(object):
    """docstring for DBInsance"""
    def __init__(self):
        super(dbInstance, self).__init__()
        self.conn = sqlite3.connect('test.db')
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS fuckUrls (ID INTEGER PRIMARY KEY, URL TEXT NOT NULL); ''')
        self.conn.commit()
        
    def checkUrlCanAdd(self,url):
        sql = "select * from fuckUrls where URL = \'%s\'" %("aaa")
        self.cur.execute(sql)
        r = self.cur.fetchone()
        if r == None:
            return True
        return False
    def insertUrlIntoDB(self,url):
        sql = "insert into fuckUrls(URL) VALUES(\'%s\')" %(url)
        self.cur.execute(sql)
        self.conn.commit()

dbSingle = dbInstance()