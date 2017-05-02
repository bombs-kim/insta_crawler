# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PostItem(scrapy.Item):
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

    @staticmethod
    def create(post):
        return PostItem(media_id=post['id'],
                         url='https://www.instagram.com/p/%s/' % post['code'],
                         date=post['date'],
                         comment_count=post['comments']['count'],
                         like_count=post['likes']['count'],
                         user_id=post['owner']['id'],
                         caption=post['caption'].replace('\n', ' ').replace('\t', ' '),
                         is_video=post['is_video'],
                         name=post['name'],
                         username=post['username'],
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
