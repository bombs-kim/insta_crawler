# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MediaItem(scrapy.Item):
    media_id = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()
    comment_count = scrapy.Field()
    like_count = scrapy.Field()
    user_id = scrapy.Field()
    caption = scrapy.Field()
    is_video = scrapy.Field()
    name = scrapy.Field()
    username = scrapy.Field()

    def __str__(self):
        return ""

    @staticmethod
    def create(media):
        return MediaItem(media_id=media['id'],
                         url='https://www.instagram.com/p/%s/' % media['code'],
                         date=media['date'],
                         comment_count=media['comments']['count'],
                         like_count=media['likes']['count'],
                         user_id=media['owner']['id'],
                         caption=media['caption'].replace('\n', ' ').replace('\t', ' '),
                         is_video=media['is_video'],
                         name=media['name'],
                         username=media['username'],
                         )


class UserItem(scrapy.Item):
    user_id = scrapy.Field()
    username = scrapy.Field()
    follows = scrapy.Field()
    followed_by = scrapy.Field()
    biography = scrapy.Field()
    full_name = scrapy.Field()
    media_count = scrapy.Field()
    profile_pic_url = scrapy.Field()

    def __str__(self):
        return ""
