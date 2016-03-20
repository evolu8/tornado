from google.appengine.api import urlfetch
from collections import Counter
from xml.etree import ElementTree as ET
import hashlib


import models
import secrets
import cryptAES


def scrape(url):
    """
    Scraper to go grab html content of requested URL
    Args:
        url:

    Returns:
        raw html of page found at URL
    """
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, url)
    text = ""
    try:
        result = rpc.get_result()
        if result.status_code == 200:
            text = result.content
    except urlfetch.DownloadError:
        # this get handled further up the flow, but more should be done here ideally
        pass
    return text


class DataInterfaceGAE():
    def insert(self, word, count):
        """
        upsert the salted hashed word, the encrypted word and the incremented count
        """
        hashed_word = hashlib.sha512(word.encode('utf-8') + secrets.salt).hexdigest()
        q = models.WordRow.query(models.WordRow.word_hash==hashed_word)
        wr = models.WordRow()
        if q.count() == 1:
            wr = q.get()
            wr.count = wr.count + count
            wr.put_async()
        else:
            ciph =  cryptAES.AESCipher()
            wr.count = count
            wr.encrypted_word = ciph.encrypt(word)
            wr.word_hash = hashed_word
            wr.put_async()
    def list(self):
        """
        lists all rows for the admin page to render
        """
        #  TODO: paginate/offset and repeate before production ready,
        #  as 100000 is the hard limit of a single fetch
        wrs = models.WordRow.query().fetch(limit=100000)
        return wrs




class DataInterfaceMySQL():
    #  TODO: MySQLdb import failing on my Mac. Will fix this if I get time.
    pass

def html2text(html):
    """
        This does not produce pretty text, but we don't need it to be.
    Args:
        html:

    Returns:
        single string of all the text within the html's text nodes.
    """
    exclude = ["script", "style"]
    # TODO: we should allow resumption on parsing errors. HTML can be broken on many sites
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.fromstring(html, parser=parser)
    resp=""

    #  some recursive fun
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
    #  this could be more sophisticated
    return str_in.split()

def list2freq(list_in):

    #  the collections Counter is extremely fast and great for this task of feq compilation on lists
    cnt = Counter(list_in)
    return dict(cnt)

def orderByFreq(list_in):
    cnt = Counter(list_in)

    return list(cnt)

def topFreq(list_in, n):
    return Counter(list_in).most_common(n)
