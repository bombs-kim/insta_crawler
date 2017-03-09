# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import socket
from spiders import json_patch


class LocalSavePipeline(object):
    def process_item(self, item, spider):
        if item.__class__.__name__ == 'MediaItem':
            item_dict = dict(item)
            filename = item_dict['name']
            del item_dict['name']
            line = json_patch.dump_json(item_dict)
            with open(spider.output_path + '/' + spider.today + '/' + filename, 'a') as f:
                f.write(line.replace('\\/', '/') + '\n')
        elif item.__class__.__name__ == 'UserItem':
            item_dict = dict(item)
            line = json_patch.dump_json(item_dict)
            with open('user_profile.dat', 'a') as f:
                f.write(line + '\n')


class FlumePipeline(object):
    def __init__(self, FLUME_SERVER_IP, FLUME_SERVER_PORT):
        self.FLUME_SERVER_IP = FLUME_SERVER_IP
        self.FLUME_SERVER_PORT = FLUME_SERVER_PORT

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            FLUME_SERVER_IP=crawler.settings.get('FLUME_SERVER_IP'),
            FLUME_SERVER_PORT=crawler.settings.get('FLUME_SERVER_PORT')
        )

    def open_spider(self, spider):
        spider.logger.info('FLUME_PIPELINE open_spider')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.FLUME_SERVER_IP, self.FLUME_SERVER_PORT))

    def close_spider(self, spider):
        spider.logger.info('FLUME_PIPELINE close_spider')
        self.sock.close()

    def process_item(self, item, spider):
        if item.__class__.__name__ == 'MediaItem':
            item_dict = dict(item)
            filename = item_dict['name']
            del item_dict['name']
            line = json_patch.dump_json(item_dict)
            self.sock.send(line.replace('\\/', '/') + '\n')
            return item
        elif item.__class__.__name__ == 'UserItem':
            item_dict = dict(item)
            line = json_patch.dump_json(item_dict)
            with open(spider.output_path + '/user_profile.dat', 'a') as f:
                f.write(line + '\n')
