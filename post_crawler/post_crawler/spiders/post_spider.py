#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import scrapy
from post_crawler.items import PostItem, UserItem
import json_patch
from datetime import datetime


USER_LOG = 'user_log.txt'
COMMENTED_POSTS_FILE = 'commented_posts.txt'


class PostSpider(scrapy.Spider):
    name = "post_spider"
    custom_settings = {
        'ITEM_PIPELINES': {
            'post_crawler.pipelines.LocalSavePipeline': 800,
        }
    }

    def __init__(self, new_kor_file="newusers.txt",
                 valid_user_file="out/user_log.txt",
                 output_path="out", default_last_crawled_id=0, flume=False):
        self.output_path = output_path  # need to change name 'output' => '?'
        self.load_user_cnt, self.valid_user_cnt = 0, 0
        self.date = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not os.path.isfile(self.output_path + '/' + USER_LOG):
            with open(self.output_path + '/' + USER_LOG, 'w'):
                pass

        self.task_list = self.load_task(
            new_kor_file, valid_user_file, default_last_crawled_id)
        self.load_user_cnt = len(self.task_list)
        self.valid_user_cnt = self.load_user_cnt
        self.logger.info('task count ::: %s' % len(self.task_list))

        if flume == 'FLUME':
            PostSpider.custom_settings['ITEM_PIPELINES'][
                'post_spider.pipelines.FlumePipeline'] = 300
        else:
            if not os.path.isdir(self.output_path + '/' + self.date):
                os.mkdir(self.output_path + '/' + self.date)

    def start_requests(self):
        for task in self.task_list:
            url = 'https://www.instagram.com/%s/' % task['username']
            meta = {'task': task, 'cursor': None }
            yield scrapy.Request(url, meta=meta,
                                 callback=self.parse_first_response)

    def close(self, reason):
        self.logger.info('#'*40)
        self.logger.info('Loaded_users     ::: %10s' % self.load_user_cnt)
        self.logger.info('Crawled_users    ::: %10s' % self.valid_user_cnt)

    def make_request(self, task, cursor=None):
        url = 'https://www.instagram.com/%s/' % task['username']
        if cursor:
            url += '?max_id=' + cursor
        else:
            # what the heck is this?
            self.logger.critical('None cursor url: %s, cursor: %s, task_max_id: %s'
                                 % (url, cursor, task['max_id']))
            url += '?max_id=' + str(task['max_id'])
        meta = {'task': task, 'cursor': cursor}
        return scrapy.Request(url, meta=meta)

    def parse_first_response(self, response):
        task = response.meta['task']
        if response.status == 404:
            if 'code' in task:
                url = 'https://www.instagram.com/p/%s/' % task['code']
                return [scrapy.Request(url, meta=response.meta, callback=self.verify_user)]
            else:
                self.logger.info('first crawl in 404 ::: %s' % task['username'])
                self.valid_user_cnt -= 1
                return

        contents = self.get_actual_contents(response.body)
        media_root = contents['entry_data']['ProfilePage'][0]['user']['media']
        user_item = [self.get_user_info(contents['entry_data']['ProfilePage'][0]['user'])]
        media_list, next_cursor, is_last_id_met = self.get_media_list(task, media_root)
        if not media_list:
            self.logger.error('FIRST RESPONSE IS NOT VALID ::: empty media_list')
            self.logger.info('VALID_USER APPEND ::: %s' % json_patch.dump_json(task))
            self.update_log(task)
            return user_item

        task['max_id'] = max([media['media_id'] for media in media_list])
        task['recent_id'] = task['max_id']
        task['code'] = media_list[-1]['url'].split('/')[-2]

        self.save_commented_posts(media_list)

        if is_last_id_met:
            self.logger.info('LAST CRAWLED ID MEET :::')
            self.update_log(task)
            return media_list + user_item + []

        if not next_cursor:
            self.logger.info('NONE CURSOR in FIRST REQUEST :::')
            self.update_log(task)
            return media_list + user_item + []
        req = self.make_request(task=task, cursor=next_cursor)
        return media_list + user_item + [req]

    def parse(self, response):
        task = response.meta['task']
        contents = self.get_actual_contents(response.body)
        media_root = contents['entry_data']['ProfilePage'][0]['user']['media']
        media_list, next_cursor, is_last_id_met = self.get_media_list(
            task, media_root)
        if is_last_id_met:
            finish_cond = 'LAST_ID_MET'
        elif next_cursor is None:
            finish_cond = 'NO_CURSOR'
        else:
            finish_cond = None

        if finish_cond:
            self.logger.info('FINISH_TASK (%s) ::: task %s'
                             % (finish_cond, task['username']))
            self.update_log(task)
            return media_list

        req = self.make_request(task=task, cursor=next_cursor)
        self.save_commented_posts(media_list)
        return media_list + [req]

    def verify_user(self, response):
        task = response.meta['task']
        if response.status == 404:
            self.logger.info('Deleted user ::: %s, post_url ::: %s'
                             % (task['username'], response.url))
            self.valid_user_cnt -= 1
        elif response.status == 200:
            contents = self.get_actual_contents(response.body)
            username = contents['entry_data']['PostPage'][0]['media']['owner']['username']
            self.logger.info('Change username ::: %s --> %s, post_url ::: %s' % (task['username'], username, response.url))
            task['username'] = username
            response.meta['task'] = task
            url = 'https://www.instagram.com/%s/' % task['username']
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_first_response)
        elif response.status >= 500 or response.status == 429:
            self.logger.info('response status ::: %s, sleep 2 sec' % response.status)
            time.sleep(2)
            yield scrapy.Request(response.url, meta=response.meta, callback=self.verify_user)
        else:
            self.logger.info('unknown error status ::: %s , url ::: %s' % (response.status, response.url))

    def update_log(self, task):
        user_log = dict()
        user_log['code'] = task['code']
        user_log['last_crawled_id'] = str(task['recent_id'])
        user_log['update_time'] = self.date
        user_log['username'] = task['username']
        data = json_patch.dump_json(user_log)
        with open(self.output_path + '/' + USER_LOG, 'a') as f:
            f.write(data + '\n')

    def load_task(self, new_kor_file, valid_user_file, default_last_crawled_id):
        username_set = set()
        task_list = []
        with open(valid_user_file) as f:
            self.logger.info('valid_user_file ::: %s' % valid_user_file)
            for line in f:
                user = json_patch.load_json(line.strip())
                username = user['username']
                if username not in username_set:
                    username_set.add(username)
                else:
                    continue
                task = dict()
                task['username'] = username
                task['last_crawled_id'] = long(user['last_crawled_id'])
                task['recent_id'] = long(user['last_crawled_id'])
                task['code'] = user['code']
                task_list.append(task)
        with open(new_kor_file) as f:
            self.logger.info('new_kor_file ::: %s' % new_kor_file)
            for line in f:
                username = line.strip()
                if username in username_set:
                    continue
                username_set.add(username)
                task = dict()
                task['username'] = username
                task['last_crawled_id'] = long(default_last_crawled_id)
                task['recent_id'] = long(default_last_crawled_id)
                task_list.append(task)
        return task_list

    def save_commented_posts(self, media_list):
        with open(self.output_path + '/'+ COMMENTED_POSTS_FILE + '.' + self.date, 'a') as f:
            for media in media_list:
                if int(media['comment_count']) > 0:
                    f.write(str(media['comment_count']) + '\t' + media['url']+'\n')

    def get_actual_contents(self, body):
        begin = body.find('window._sharedData')
        if begin == -1:
            return
        begin = body.find('{', begin)
        if begin == -1:
            return
        end = body.find('\n', begin)
        end = body.rfind('}', begin, end)
        if end == -1:
            return
        return json_patch.load_json(body[begin:end + 1])

    def get_media_list(self, task, media_root):
        media_ids, valid_media_list, is_last_id_met = set(), [], False
        if 'nodes' not in media_root:
            self.logger.info('nodes not in user ::: %s' % task['username'])
            return valid_media_list, None, is_last_id_met
        for media in media_root['nodes']:
            media_id = long(media['id'])
            media['id'] = media_id
            media_ids.add(media_id)
            if task['last_crawled_id'] >= media_id and False:
                is_last_id_met = True
                self.logger.info('last_crawled_id=%s, media_id=%s' % (task['last_crawled_id'], media_id))
                break

            date = datetime.fromtimestamp(media['date']).strftime('%Y-%m-%dT%H%M%S')
            media['date'] = date
            if 'caption' not in media:
                media['caption'] = ''
            media['username'] = task['username']
            media['name'] = (task['username'] + '.jl').encode('utf-8')  # filename <= need to be fixed
            valid_media_list.append(PostItem.create(media))
        if media_root['page_info']['has_next_page']:
            next_cursor = media_root['page_info']['end_cursor']
        else:
            next_cursor = None
        return valid_media_list, next_cursor, is_last_id_met

    def get_user_info(self, contents):
        item = UserItem()
        item['username'] = contents['username']
        item['user_id'] = contents['id']
        item['biography'] = contents['biography']
        item['follows'] = contents['follows']['count']
        item['followed_by'] = contents['followed_by']['count']
        item['full_name'] = contents['full_name']
        item['media_count'] = contents['media']['count']
        item['profile_pic_url'] = contents['profile_pic_url']
        return item
