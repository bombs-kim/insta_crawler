#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import scrapy
from post_crawler.items import MediaItem, UserItem
from post_crawler import pipelines
import json_patch
from datetime import datetime

USER_LOG = 'user_log.dat'
VALID_USER = 'crawl_valid_users.dat'
COMMENT_MEDIA = 'comments_media.dat'
CRAWL_REPORT = 'crawl_report.dat'
MAX_RETRY_NUM = 5

RETRY_STATUS = [408, 429, 500, 502, 503]


class PostCrawler(scrapy.Spider):
    name = "post_crawler"
    
    custom_settings = {
        'ITEM_PIPELINES': {
            #'user_media_crawler.pipelines.LocalSavePipeline' : 800,
            #'user_media_crawler.pipelines.FlumePipeline': 300,
        }
    }

    def __init__(self, new_kor_file="", valid_user_file="", output_path="./users_log", deadline=0, flume=False):

        self.output_path = output_path
        self.need_to_sleep = True

        [self.load_user_cnt, self.valid_user_cnt, self.delete_user_cnt, self.change_username_cnt, self.new_kor_cnt,
         self.media_cnt] = 0, 0, 0, 0, 0, 0

        self.today = datetime.now().strftime('%Y%m%d_%H%M%S')

        if not os.path.isfile(self.output_path + '/' + USER_LOG):
            with open(self.output_path + '/' + USER_LOG, 'w') as f:
                f.write("")

        self.task_list = self.load_task(new_kor_file, valid_user_file, deadline)
        self.new_kor_valid_cnt = self.new_kor_cnt
        self.load_user_cnt = len(self.task_list)
        self.valid_user_cnt = self.load_user_cnt
        self.logger.info('task count ::: %s' % len(self.task_list))

        if flume == 'FLUME':
            self.logger.info('FLUME pipelines settings')
            UserMediaCrawler.custom_settings['ITEM_PIPELINES'][
                'user_media_crawler.pipelines.FlumePipeline'] = 300
        else:
            self.logger.info('Local Save pipelines settings')
            UserMediaCrawler.custom_settings['ITEM_PIPELINES'][
                'user_media_crawler.pipelines.LocalSavePipeline'] = 800
            self.logger.info('Pipeline ::: %s' % UserMediaCrawler.custom_settings['ITEM_PIPELINES'])
            if not os.path.isdir(self.output_path + '/' + self.today):
                os.mkdir(self.output_path + '/' + self.today)

    def start_requests(self):
        for task in self.task_list:
            url = 'https://www.instagram.com/%s/' % task['username']
            meta = {
                'task': task,
                'retry': 0,
                'cursor': None,
                'handle_httpstatus_all': True,  #######
            }
            yield scrapy.Request(url, meta=meta, callback=self.parse_first_response)

    def close(self, reason):
        self.logger.info('####################################')
        self.logger.info('load_task       ::: %10s' % self.load_user_cnt)
        self.logger.info('Valid User      ::: %10s' % self.valid_user_cnt)
        self.logger.info('Delete User     ::: %10s' % self.delete_user_cnt)
        self.logger.info('new kor user    ::: %10s' % self.new_kor_cnt)
        self.logger.info('new kor valid   ::: %10s' % self.new_kor_valid_cnt)
        self.logger.info('change username ::: %10s' % self.change_username_cnt)
        self.logger.info('Media count     ::: %10s' % self.media_cnt)
        self.logger.info('####################################')
        with open(self.output_path + '/' + CRAWL_REPORT, 'a') as fw:
            fw.write('##### %s #####\n' % self.today)
            fw.write('load_task       ::: %10s\n' % self.load_user_cnt)
            fw.write('Valid User      ::: %10s\n' % self.valid_user_cnt)
            fw.write('Delete User     ::: %10s\n' % self.delete_user_cnt)
            fw.write('new kor user    ::: %10s\n' % self.new_kor_cnt)
            fw.write('new kor valid   ::: %10s\n' % self.new_kor_valid_cnt)
            fw.write('change username ::: %10s\n' % self.change_username_cnt)
            fw.write('Media count     ::: %10s\n' % self.media_cnt)

    def parse(self, response):

        task, cursor, retry = [response.meta[x] for x in ['task', 'cursor', 'retry']]

        if response.status != 200:
            return self.process_response_error(task, cursor, retry, response.url,
                                               'response status is %d' % response.status)
        else:
            try:
                return self.process_response(task, response)
            except Exception as e:
                return self.process_response_error(task, cursor, retry, response.url, str(e))
            except:
                return self.process_response_error(task, cursor, retry, response.url, 'unknown exception')

    def make_first_request(self):
        req_list = []
        for task in self.task_list:
            url = 'https://www.instagram.com/%s/' % task['username']
            meta = {
                'task': task,
                'retry': 0,
                'cursor': None,
                'handle_httpstatus_all': True,
            }
            req_list.append(scrapy.Request(url, meta=meta, callback=self.parse_first_response))

        return req_list

    def make_request(self, task, cursor=None, retry=0):

        url = 'https://www.instagram.com/%s/' % task['username']

        if cursor:
            url += '?max_id=' + cursor
        else:
            self.logger.critical('cursor is None!!!!!  url : %s, cursor : %s, task_max_id : %s' \
                                 % (url, cursor, task['max_id']))
            url += '?max_id=' + str(task['max_id'])

        meta = {
            'task': task,
            'retry': retry,
            'cursor': cursor,
            'handle_httpstatus_all': True,
        }

        if retry > 0:
            self.logger.info('retry url ::: %s, retry ::: %s' % (url, retry))
            return scrapy.Request(url, meta=meta, dont_filter=True)
        else:
            return scrapy.Request(url, meta=meta)

    def parse_first_response(self, response):
        task = response.meta['task']
        if response.status == 404:
            if 'code' in task:
                url = 'https://www.instagram.com/p/%s/' % task['code']
                return [scrapy.Request(url, meta=response.meta, callback=self.verifying_user)]
            else:
                self.logger.info('first crawl in 404 ::: %s' % task['username'])
                self.new_kor_valid_cnt -= 1
                self.valid_user_cnt -= 1
                return
        elif response.status in RETRY_STATUS: 
            self.logger.info('First response status error ::: %s' % response.status)
            time.sleep(5)
            return [scrapy.Request(response.url, meta=response.meta, callback=self.parse_first_response, dont_filter=True)]

        contents = self.get_actual_contents(response.body)

        media_root = contents['entry_data']['ProfilePage'][0]['user']['media']
        
        user_item = [self.get_user_info(contents['entry_data']['ProfilePage'][0]['user'])]

        media_list, next_cursor, is_last_id_meet, under_count = self.get_media_list(task, media_root)

        if not media_list:
            self.logger.error('FIRST RESPONSE IS NOT VALID ::: empty media_list')
            self.logger.info('VALID_USER APPEND ::: %s' % json_patch.dump_json(task))
            self.update_log(task)
            return user_item
        else:
            task['max_id'] = max([media['media_id'] for media in media_list])
            task['recentId'] = max([media['media_id'] for media in media_list])
            task['code'] = media_list[-1]['url'].split('/')[-2]

        self.comment_post_output(media_list)

        if is_last_id_meet:
            self.logger.info('LAST CRAWLED ID MEET ::: (%s == media_list len:%s)' % (task['recentId'], len(media_list)))
            self.update_log(task)
            self.media_cnt += len(media_list)
            return media_list + user_item + []

        request_list = []
        if next_cursor:
            request_list.append(self.make_request(task=task, cursor=next_cursor))
        else:
            self.logger.info('NON CURSOR in FIRST REQUEST ::: (%s == media_list len:%s)' % (task['recentId'], len(media_list)))
            self.update_log(task)
            self.media_cnt += len(media_list)
            return media_list + user_item + []

        self.media_cnt += len(media_list)
        return media_list + user_item + request_list

    def process_response(self, task, response):
        contents = self.get_actual_contents(response.body)
        media_root = contents['entry_data']['ProfilePage'][0]['user']['media']
        media_list, next_cursor, is_last_id_meet, under_count = self.get_media_list(task, media_root)

        if is_last_id_meet:
            finish_cond = 'LAST_ID_MEET'
        elif under_count == len(media_list):
            finish_cond = 'ALL_MEDIA_UNDER'
        elif next_cursor is None:
            finish_cond = 'NO_CURSOR'
        else:
            finish_cond = False

        request_list = []
        if finish_cond:
            self.logger.info('FINISH_TASK (%s) ::: task %s, max_id %ld' \
                             % (finish_cond, task['username'], task['max_id']))
            self.update_log(task)
        else:
            request_list.append(self.make_request(task=task, cursor=next_cursor))

        self.need_to_sleep = 0
        self.sleep_time = 10
        self.comment_post_output(media_list)
        self.media_cnt += len(media_list)
        return media_list + request_list

    def verifying_user(self, response):
        task = response.meta['task']
        if response.status == 404:
            self.logger.info('Delete user ::: %s, post_url ::: %s' % (task['username'], response.url))
            self.delete_user_cnt += 1
            self.valid_user_cnt -= 1
        elif response.status == 200:
            contents = self.get_actual_contents(response.body)
            username = contents['entry_data']['PostPage'][0]['media']['owner']['username']
            self.logger.info('Change username ::: %s --> %s, post_url ::: %s' % (task['username'], username, response.url))
            self.change_username_cnt += 1
            task['username'] = username 
            response.meta['task'] = task
            url = 'https://www.instagram.com/%s/' % task['username']
            yield scrapy.Request(url, meta=response.meta, callback=self.parse_first_response)
        elif response.status >= 500 or response.status == 429:
            self.logger.info('response status ::: %s, sleep 2 sec' % response.status)
            time.sleep(2)
            yield scrapy.Request(response.url, meta=response.meta, callback=self.verifying_user)
        else:
            self.logger.info('unknown error status ::: %s , url ::: %s' % (response.status, response.url))

    def update_log(self, task):
        user_log = dict()
        user_log['code'] = task['code']
        user_log['last_crawled_id'] = str(task['recentId'])
        user_log['update_time'] = self.today
        user_log['username'] = task['username']
        data = json_patch.dump_json(user_log)
        with open(self.output_path + '/' + USER_LOG, 'a') as f:
            f.write(data + '\n')
        with open(self.output_path + '/' + VALID_USER + '.' + self.today, 'a') as fw:
            fw.write(data + '\n')

    def process_response_error(self, task, cursor, retry, url, error_code):

        error_msg = 'task %s, max_id %ld, retry %d, url %s, error_msg %s' \
                    % (task['username'], task['max_id'], retry, url, error_code)

        if retry >= self.need_to_sleep:
            self.logger.warning('SLEEP ::: %d sec' % (self.sleep_time * (2 ** retry)))
            time.sleep(self.sleep_time * (2 ** retry))
            self.need_to_sleep += 1

        if retry < MAX_RETRY_NUM:
            self.logger.warning('RETRY ::: ' + error_msg)
            return self.make_request(task=task, cursor=cursor, retry=retry + 1)
        else:
            self.logger.error('TOO MANY RETRY ::: ' + error_msg)
            self.logger.critical('Finished Task ::: %s' % task['username'])

    def load_task(self, new_kor_file, valid_user_file, deadline):
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
                task['recentId'] = long(user['last_crawled_id'])
                task['seen_ids'] = set([long(user['last_crawled_id'])])
                task['code'] = user['code']
                task_list.append(task)

        with open(new_kor_file) as f:
            self.logger.info('new_kor_file ::: %s' % new_kor_file)
            for line in f:
                username = line.strip()
                if username not in username_set:
                    username_set.add(username)
                else:
                    continue
                task = dict()
                task['username'] = username
                task['last_crawled_id'] = long(deadline)
                task['recentId'] = long(deadline)
                task['seen_ids'] = set([])
                task_list.append(task)
                self.new_kor_cnt += 1
        
        return task_list

    def comment_post_output(self, media_list):
        with open(self.output_path+'/'+COMMENT_MEDIA+'.'+self.today, 'a') as f:
            for media in media_list:
                if int(media['comment_count']) > 0:
                    f.write(str(media['comment_count']) + '\t' + media['url']+'\n')

    def get_actual_contents(self, body):
        """
        html body에서 실제 데이터 영역을 추출하여 json 객체로 변환
        가정 : body에서 실제 데이터 영역은 한 라인이며, " ... window._sharedData = { ... } " 형식으로 되어 있다고 가정
        """

        beg = body.find('window._sharedData')
        if beg == -1:
            return None

        beg = body.find('{', beg)
        if beg == -1:
            return None

        end = body.find('\n', beg)
        end = body.rfind('}', beg, end)
        if end == -1:
            return None

        return json_patch.load_json(body[beg:end + 1])

    def get_media_list(self, task, media_root):

        media_ids, valid_media_list, is_last_id_meet, under_count = set(), [], False, 0
        if 'nodes' not in media_root:
            self.logger.info('nodes not in user ::: %s' % task['username']) 
            return valid_media_list, None, is_last_id_meet, under_count
        for media in media_root['nodes']:

            media_id = long(media['id'])
            media['id'] = media_id
            media_ids.add(media_id)

            if task['last_crawled_id'] == media_id:
                self.logger.info('last_crawled_id detect=%s' % media_id)
                is_last_id_meet = True
                break

            if task['last_crawled_id'] >= media_id:
                self.logger.info('[UNDER] last_crawled_id=%s, media_id=%s' % (task['last_crawled_id'], media_id))
                under_count += 1

            if media_id in task['seen_ids']:
                self.logger.info('INTRA_SEEN_MEDIA_ID ::: task %s, max_id %ld, dup_id %ld' \
                                  % (task['username'], task['max_id'], media_id))
                continue
            task['seen_ids'].add(media_id)
            date = datetime.fromtimestamp(media['date']).strftime('%Y-%m-%dT%H%M%S')
            media['date'] = date
            if 'caption' not in media:
                media['caption'] = ''
            media['username'] = task['username']
            media['name'] = (task['username'] + '.dat').encode('utf-8')

            valid_media_list.append(MediaItem.Create(media))
        if media_root['page_info']['has_next_page']:
            next_cursor = media_root['page_info']['end_cursor']
        else:
            next_cursor = None

        return valid_media_list, next_cursor, is_last_id_meet, under_count
    
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
