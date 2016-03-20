from google.appengine.api import urlfetch
from collections import Counter
from xml.etree import ElementTree as ET
import hashlib


import models
import settings
import cryptAES


def scrape(url):
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, url)
    text = ""
    try:
        result = rpc.get_result()
        if result.status_code == 200:
            text = result.content
    except urlfetch.DownloadError:
        pass
    return text


class DataInterfaceGAE():
    def insert(self, word, count):
        hashed_word = hashlib.sha512(word + settings.salt).hexdigest()
        q = models.WordRow.query(models.WordRow.word_hash==hashed_word)
        wr = models.WordRow()
        if q.count() == 1:
            wr = q.get()
            wr.count += count
            wr.put_async()
        else:
            ciph =  cryptAES.AESCipher()
            wr.count += count
            wr.encrypted_word = ciph.encrypt(word)
            wr.word_hash = hashed_word
            wr.put_async()
    def list(self):
        wrs = models.WordRow.query().fetch(limit=100000)
        return wrs




class DataInterfaceMySQL():
    #MySQLdb import failing on my Mac. Will fix this if I get time.
    pass

def html2text(html):
    #parser = MyHTMLParser()
    exclude = ["script", "style"]
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.fromstring(html, parser=parser)
    resp = ""
    def walk(el):
        resp = ""
        for i in el:
            resp += walk(i) + " "
        if el.tag not in exclude and el.text is not None:
            resp += el.text + " "
        return resp
    resp = walk(tree)
    return resp

def str2words(str_in):
    return str_in.split()

def list2freq(list_in):
    cnt = Counter(list_in)
    return dict(cnt)

def orderByFreq(list_in):
    cnt = Counter(list_in)

    return list(cnt)

def topFreq(list_in, n):
    return Counter(list_in).most_common(n)
