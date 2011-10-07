#!/usr/bin/env python
#author:Richard Peng
#project:Kindelabra
#website:http://www.richardpeng.com/projects/kindelabra/
#repository:https://github.com/richardpeng/Kindelabra
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

import hashlib
import os
import re
import json
import sys
import datetime

import ebook

KINDLEROOT = '/mnt/us'
FILTER = ['pdf', 'mobi', 'prc', 'txt', 'tpz', 'azw1', 'azw', 'manga', 'azw2']
FOLDERS = ['documents', 'pictures']

class Collection(dict):
    def __init__(self, arg = None):
        if arg == None:
            arg = { 'locale': 'en-US', 'items': [], 'lastAccess': 0}
        super(Collection, self).__init__(arg)

    '''Holds a single collection
    '''
    def has_hash(self, filehash):
        return filehash in self['items']

    def add_hash(self, filehash):
        self['items'].append(filehash)

    def remove_hash(self, filehash):
        self['items'].remove(filehash)

class CollectionDB(dict):
    '''Holds a collection database
    '''
    def __init__(self, colfile = None):
        if colfile == None:
            return
        with open(colfile) as colfile:
            tmpjson = json.load(colfile)
            tmpdict = dict()
            for key in iter(tmpjson.keys()):
                split = key.rpartition('@')
                colname = unicode(split[0])
                tmpdict[colname] = Collection(tmpjson[key])
                tmpdict[colname]['locale'] = split[2]
            dict.__init__(self, tmpdict)

    # Converts the collection back to Kindle JSON format
    def toKindleDb(self):
        tmpjson = dict()
        for key in self:
            tmpkey = '@'.join([key, self[key]['locale']])
            tmpvalue = self[key].copy()
            del tmpvalue['locale']
            tmpjson[tmpkey] = tmpvalue
        return tmpjson

    def in_collection(self, collection, ebook):
        return self[collection].has_hash(ebook.fileident())

    def add_ebook(self, collection, ebook):
        self[collection].add_hash(ebook.fileident())

class Ebook():
    def __init__(self, path):
        self.path = get_kindle_path(path)
        self.hash = get_hash(self.path)
        self.title = None
        self.meta = None
        self.asin = None
        self.type = None
        self.author = None
        ext = os.path.splitext(path)[1][1:].lower()
        if ext in ['mobi', 'azw']:
            self.meta = ebook.Mobi(path)
            if self.meta.title:
                self.title = self.meta.title
                if 100 in self.meta.exth:
                    self.author = self.meta.exth[100]
                if 113 in self.meta.exth:
                    self.asin = self.meta.exth[113]
                if 501 in self.meta.exth:
                    self.type = self.meta.exth[501]
                if 503 in self.meta.exth:
                    self.title = self.meta.exth[503]
            else:
                print "\nMetadata read error:", path
        elif ext in ['tpz', 'azw1']:
            self.meta = ebook.Topaz(path)
            if self.meta.title:
                self.title = self.meta.title
                if self.meta.asin:
                    self.asin = self.meta.asin
                if self.meta.type:
                    self.type = self.meta.type
            else:
                print "\nTopaz metadata read error:", path
        elif ext in ['azw2']:
            self.meta = ebook.Kindlet(path)
            if self.meta.title:
                self.title = self.meta.title
            if self.meta.asin:
                self.asin = self.meta.asin
                self.type = 'AZW2'
            else:
                # Couldn't get an ASIN, developper app? We'll use the hash instead, which is what the Kindle itself does, so no harm done.
                print "\nKindlet Metadata read error, assuming developper app:", path
    
    def fileident(self):
        if self.asin == None:
            return '*'+self.hash
        else:
            return "#%s^%s" % (self.asin, self.type)

class Kindle:
    '''Access a Kindle filesystem
    '''
    def __init__(self, root):
        self.root = unicode(root)

    def init_data(self):
        self.files = dict()
        self.filetree = dict()
        if self.is_connected():
            for folder in FOLDERS:
                self.load_folder(folder)

            for path in self.files:
                regex = re.compile(r'.*?/(%s)' % '|'.join(FOLDERS))
                self.get_filenodes(self.filetree, re.sub(regex, r'\1', self.files[path].path).split('/'))

    def load_folder(self, path):
        sys.stdout.write("Loading " + path)
        for root, dirs, files in os.walk(os.path.join(self.root, path)):
            for filename in files:
                if os.path.splitext(filename)[1][1:].lower() in FILTER:
                    fullpath = os.path.abspath(os.path.join(root, filename))
                    book = Ebook(fullpath)
                    self.files[book.hash] = book
                    sys.stdout.write(".")
                    sys.stdout.flush()
        sys.stdout.write("\n")

    def searchAsin(self, asin):
        '''Returns the Ebook with asin
        '''
        for filehash in self.files:
            if self.files[filehash].asin == asin:
                asin_hash = self.files[filehash]
                break
            else:
                asin_hash = None
        return asin_hash

    # Adds files to the dictionary: tree
    def get_filenodes(self, tree, nodes):
        if len(nodes) > 1:
            if not nodes[0] in tree:
                tree[nodes[0]] = dict()
            self.get_filenodes(tree[nodes[0]], nodes[1:])
        elif len(nodes) == 1:
            if not 'files' in tree:
                tree['files'] = list()
            tree['files'].append(nodes[0])

    # Checks if the specified folder is a Kindle filestructure
    def is_connected(self):
        docs = os.path.exists(os.path.join(self.root, 'documents'))
        sys = os.path.exists(os.path.join(self.root, 'system'))
        return docs and sys

    def getDb(self):
        colfile = os.path.join(self.root, 'system', 'collections.json')
        return CollectionDB(colfile)
    
    def saveDb(self, db):
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup = os.path.join(self.root, 'system', '%s-collections.json.backup' % (now))
        jsonfile = os.path.join(self.root, 'system', 'collections.json')
        if os.path.exists(jsonfile):
            os.rename(jsonfile, backup)
        with open(os.path.join(self.root, 'system', 'collections.json'), 'wb') as colfile:
            json.dump(db.toKindleDb(), colfile, separators=(',', ':'), ensure_ascii=True)

# Returns a full path on the kindle filesystem
def get_kindle_path(path):
    path = os.path.normpath(path)
    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    return '/'.join([KINDLEROOT, re.sub(r'.*(documents|pictures)', r'\1', folder), filename]).replace('\\', '/')

# Returns a SHA-1 hash
def get_hash(path):
    path = unicode(path).encode('utf-8')
    return hashlib.sha1(path).hexdigest()

if __name__ == "__main__":
    k = Kindle("Kindle")
    k.init_data()
