# -*- coding: utf-8 -*-
# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class InstaUserItem(scrapy.Item):
    username = scrapy.Field()
    last_post_id = scrapy.Field()
    last_crawled_date = scrapy.Field()
    user_freq = scrapy.Field()
    code = scrapy.Field()

    follows_count = scrapy.Field()
    followed_by_count = scrapy.Field()
    profile = scrapy.Field()
    full_name = scrapy.Field()
    user_id = scrapy.Field()
    origin_comment = scrapy.Field()
    my_depth = scrapy.Field()
    last_post_date = scrapy.Field()
    captions = scrapy.Field()
    lan = scrapy.Field()
    kor_len = scrapy.Field()
    kor_ratio = scrapy.Field()

    def __str__(self):
        return ""


class InstaPostItem(scrapy.Item):
    user_id = scrapy.Field()
    comments_count = scrapy.Field()
    caption = scrapy.Field()
    likes_count = scrapy.Field()
    date = scrapy.Field()
    is_video = scrapy.Field()
    id = scrapy.Field()
    url = scrapy.Field()
    username = scrapy.Field()

    def __str__(self):
        return ""

class InstaIdentifiedUserItem(scrapy.Item):
    user = scrapy.Field()
    nodes = scrapy.Field()

    def __str__(self):
        return ""
