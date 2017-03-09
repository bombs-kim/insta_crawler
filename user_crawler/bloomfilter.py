#!/usr/bin/env python
# -*- coding: utf8 -*-

import resource

from pybloomfilter import BloomFilter
from datetime import datetime


class BloomFilterControl:
    def __init__(self, filename, capacity=30000000, error_rate=0.00001):
        startMem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        with open(filename, 'a'):  # touch file
            pass
        self.bf = self.load_bf(filename, capacity, error_rate)
        bfMem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print 'bloom filter Mem size : %s' % (bfMem-startMem)
        self.filename = filename

    def load_bf(self, filename, capacity, error_rate):
        bf = BloomFilter(capacity=capacity, error_rate=error_rate)
        with open(filename) as f:
            for line in f:
                bf.add(line.split('\t')[0].strip())
        return bf

    def __contains__(self, item):
        if item in self.bf:
            return True
        else:
            return False
    """
    def check_item(self, item):
        if item in self.bf:
            return True
        else:
            return False
    """
    def add_item(self, item):
        if item not in self.bf:
            self.bf.add(item)
            with open(self.filename, 'a') as f:
                f.write(item+'\n')


def load_items(filename):
    items = set([])
    with open(filename) as f:
        for line in f:
            items.add(line.strip())
    return items


if __name__ == "__main__":
    print datetime.now()
    bfc = BloomFilterControl('kor-guess.txt', 100000000, 0.000001)
    print datetime.now()
