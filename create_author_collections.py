from kindle import *
from sys import argv

k = Kindle(argv[1])
k.init_data()
try:
	db = k.getDb()
except (IOError, ValueError):
	db = CollectionDB()

created = []

for e in k.files.values():
	if e.author == None or e.author == "Unknown":
		continue
	a = "_" + e.author
	if a not in db:
		db[a] = Collection()
		created.append(a)
	if not db.in_collection(a, e):
		db.add_ebook(a, e)
	print a, e.title, db[a]

for a in created:
	if db[a].count() < 3:
		del db[a]

k.saveDb(db)
