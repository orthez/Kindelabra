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

	a = e.author
	if a.find(",")!=-1:
		names = [x.strip() for x in a.split(",")]
		if len(names) == 2:
			a = names[1] + " " + names[0]
	a = "_" + a
	if a not in db:
		db[a] = Collection()
		created.append(a)
	if not db.in_collection(a, e):
		db.add_ebook(a, e)
	print a, e.title

for a in created:
	if db[a].count() < 3:
		del db[a]

k.saveDb(db)
