# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import codecs
# from insta_general.items import InstaUserItem, InstaPostItem


class InstaPostPipeline(object):
    def process_item(self, item, spider):
        #if not isinstance(item, InstaPostItem):
        #    return item
        f = spider.postfp
        json.dump(dict(item), f, ensure_ascii=False)
        f.write('\n')
        return item


class IdentifiedUserPipeline(object):
    def process_item(self, item, spider):
        filename = spider.path + ('posts/%s.jl' % item["username"])
        f = open_utf8(filename, 'a')
        for post in item["nodes"]:
            json.dump(post, f, ensure_ascii=False)
            f.write('\n')
        f.close()

def open_utf8(path, mode):
    try:
        f = codecs.open(path, mode, encoding='utf-8')
    except IOError as e:
        print "\n\n\nerror occured %s\n\n\n" % path
        print e.message
    else:
        return f

"""
class InstaUserPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, InstaUserItem):
            return item
        #uf = spider.userfp
        kf = spider.KOR_user_fp
        #json.dump(dict(item), uf, ensure_ascii=False)
        json.dump(dict(item), kf, ensure_ascii=False)
        #uf.write('\n')
        kf.write('\n')
        return item

    # remove duplicates
    # and leave the most recent entries
    def removeDuplicate(self, fp):
        "removing duplicate now!"
        filename = fp.name
        d = {}
        i = 0
        try:
            with open(filename, 'r') as f:
                for line in f:
                    j = json.loads(line)
                    username = j["username"]
                    if d.get(username):
                        i += 1
                    d[username] = j
            print "number of overwrites on total_users: %d" % i
            with codecs.open(filename, 'w', 'utf-8') as f:
                for key in d:
                    json.dump(d[key], f, ensure_ascii=False)
                    f.write('\n')
        except IOError:
            print "IO error in removing duplicates"
            return

    def close_spider(self, spider):
        self.removeDuplicate(spider.KOR_user_fp)
"""