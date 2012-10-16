#coding: utf-8
from common import notify_page
import urllib
import time
import random

for i in xrange(1000000):
    try: notify_page(1, "r_%s" % i)
    except: pass
    if random.random() < 1:
        notify_page(1, "o_%s" % random.randint(1, 100))
    time.sleep(2)
