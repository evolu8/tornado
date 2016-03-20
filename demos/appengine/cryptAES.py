

import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

import secrets



class AESCipher(object):
    """
    Mostly lifted from SO, but ammended to cope with UTF-8 text, and to allow configurable or passable secrets.
    AES is very strong, so the weakest link in this armour is the management of the secrets. See the README for more.

    I've also added more explanation.
    """
    def __init__(self, key=secrets.secret):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        # raw is no good as we need predictable length, so first unify to unicode, then b64 to something managable
        prepped = base64.b64encode(raw.encode('utf-8'))
        prepped = self._pad(prepped)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(prepped))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        # iv allows the same text to be encrypted to different result data, making many collision attacks impossible
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        # remember we prepped the input, so we need to undo that
        return base64.b64decode(self._unpad(cipher.decrypt(enc[AES.block_size:]))).decode('utf-8')

    def _pad(self, s):
        # again, we need lengths divisable by the block size, so we pad and unpad
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]