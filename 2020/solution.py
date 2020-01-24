import sys
sys.path.insert(0, '../2019/solution')

from Database import Database

db = Database()
with open('small-body-db.csv') as finput:
    db.read_from_csv(finput)


