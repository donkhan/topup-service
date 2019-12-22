import hashlib

def md5(s):
    m = hashlib.md5()
    m.update(s)
    md5 = m.hexdigest()
    return md5