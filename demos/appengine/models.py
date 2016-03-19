from google.appengine.ext import ndb

class WordRow(ndb.Model):
  """Models an individual Guestbook entry with content and date."""
  word_hash = ndb.StringProperty(indexed=True)
  encrypted_word = ndb.StringProperty(indexed=False)
  count = ndb.IntegerProperty(indexed=False)