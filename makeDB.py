import sqlite3

conn = sqlite3.connect('test.db')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS fuckUrls (ID INTEGER PRIMARY KEY, URL TEXT NOT NULL); ''')
conn.commit()
baidu = "https://www.baidu.com"
sql = "insert into fuckUrls(URL) VALUES(\'%s\')" %(baidu)

cur.execute(sql)
conn.commit()


sql = "select * from fuckUrls where URL = \'%s\'" %(baidu)
cur.execute(sql)
r = cur.fetchone()
print(r)


sql = "select * from fuckUrls where URL = \'%s\'" %("aaa")
cur.execute(sql)
r = cur.fetchone()
print(r)

conn.close()