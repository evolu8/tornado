from google.appengine.ext import ndb

class WordRow(ndb.Model):
  """equivolent of a row in MySQL"""
  word_hash = ndb.StringProperty(indexed=True)
  encrypted_word = ndb.StringProperty(indexed=False)
  count = ndb.IntegerProperty(indexed=False)