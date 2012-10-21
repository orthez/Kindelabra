from kindle import *
from sys import argv, exit

if len(argv) == 1:
	print "Usage: %s <kindle root folder>"%argv[0]
	exit(-1)

k = Kindle(argv[1])
k.init_data()
try:
	db = k.getDb()
except (IOError, ValueError):
	print "Error getting collection, making one up"
	db = CollectionDB() # Good for debug, shouldn't happen in real life

created = []

sample = "__Samples"

for e in k.files.values(): # get all the ebooks, don't care about their keys
	# Skip things that don't have an author
	if e.author == None or e.author == "Unknown":
		continue

	a = e.author
	if a.find(",")!=-1:
		# re-order "Last, First" authors into "First, Last" order
		names = [x.strip() for x in a.split(",")]
		if len(names) == 2: # Some other cases will be got, but this skips most of them
			a = names[1] + " " + names[0]

	a = "_" + a # Put these collections before everything else (well, unless it's got >1 '_')
	if a not in db:
		db[a] = Collection()
		created.append(a)
	if not db.in_collection(a, e):
		db.add_ebook(a, e)

	if e.sample:
		if sample not in db:
			db[sample] = Collection()
		if not db.in_collection(sample, e):
			db.add_ebook(sample, e)

	print a, e.title

for a in created:
	if db[a].count() < 3: # Don't want collection for *every* author, just those I've got >=3 books for
		del db[a] # Note that we're only doing this for ones we made earlier

k.saveDb(db)
