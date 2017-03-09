# -*- coding: utf-8 -*-
import scrapy
import os
import codecs
import json
from scrapy import Request
from datetime import datetime
from pybloomfilter import BloomFilter
import lantype


class NewUserCrawlerSpider(scrapy.Spider):
    name = "new_user_crawler"
    allowed_domains = ["www.instagram.com"]
    start_urls = (
        'http://www.www.instagram.com/',
    )
    baseurl = 'https://www.instagram.com/%s/'
    date = datetime.now().strftime("%Y%m%d_%H%M%S")

    def __init__(self, kor_file="test/user_log.dat",
                 non_kor_file="test/non_kor.dat",
                 new_kor_path="test/",
                 post_urls_file='test/comments_media.dat',
                 comments_eq_or_more='1'):
        self.NON_KOR_file = non_kor_file
        self.new_KOR_path = os.path.join(new_kor_path,  '')

        self.KOR_users = loadUsers(kor_file)
        self.NON_KOR_users = loadUsers(non_kor_file)
        self.new_KOR_users = set()
        self.new_NON_KOR_users = set()
        self.KOR_guess_users = set()

        self.post_urls = loadPostUrls(
            post_urls_file, comments_eq_or_more)

    def start_requests(self):
        for idx, url in enumerate(self.post_urls):
            yield Request(url)
            if idx % 1000 == 0:
                print idx

    def parse(self, response):
        j = decodeJsonInResponse(response)
        nodes = searchAllNested(j, "comments nodes")[0]
        owner_name = searchAllNested(j, "owner username")[0]
        for comment in nodes:
            user = comment["user"]
            user_id = user["id"]
            username = user["username"]
            if(username in self.KOR_users or ##
               username in self.NON_KOR_users or ##
               username in self.KOR_guess_users):
                    continue
            text = comment["text"]
            lan = getCommentLan(text)
            if lan != lantype.KOR_GUESS:
                continue
            self.KOR_guess_users.add(user_id)
            # self.logger.info("guess user %s added by %s"
            #                  % (username, owner_name))
            # make a request to this KOR_GUESS user
            url = self.baseurl % username
            yield Request(url, callback=self.parse_profile_page)

    def parse_profile_page(self, response):
        # Json parsing Errors
        try:
            j = decodeJsonInResponse(response)
        except UnboundLocalError:
            self.logger.info('UnboundLocalError')
            return

        user = searchAll(j, "user")[0]
        username = user["username"]
        user_id = user["id"]

        temp = searchAll(j, "nodes")
        if user["is_private"] or not temp:
            return
        nodes = temp[0]

        captions = []
        for post in nodes:
            captions.append(post.get('caption'))
            code = post['code']
        lan, kor_len, kor_ratio = getCapsLan(captions)
        if lan == lantype.KOR:
            self.KOR_users.add(username) ##
            self.new_KOR_users.add(username)
            # self.logger.info("KOR user %s added", username)
        elif lan == lantype.NON_KOR:
            if username not in self.NON_KOR_users:
                self.NON_KOR_users.add(username)  # user_id?
                self.new_NON_KOR_users.add((username, user_id, code))
                self.logger.info("NON_KOR user: %s - len: %d, ratio:%s"
                    % (username, kor_len, kor_ratio))
        else:
            self.logger.info("UNKNOWN user: %s - len: %d, ratio:%s"
                % (username, kor_len, kor_ratio))

    def closed(self, reason):
        with open(self.new_KOR_path + "new_kor_users.dat.%s"
                  % self.date, 'w') as f:
            for username in self.new_KOR_users:
                f.write(username + '\n')
        with open(self.NON_KOR_file, 'a') as f:
            for username, user_id, code in self.new_NON_KOR_users:
                j = json.dumps(
                    {'username' : username, 'user_id' : user_id, 'code': code})
                f.write(j + '\n')


def loadUsers(filename):
    usernames = BloomFilter(capacity=30000000, error_rate=0.00001)
    try:
        with open(filename, 'r') as f:
            for line in f:
                username = str(json.loads(line.strip())["username"])
                usernames.add(username)
    except IOError:
        print "file doesn't exist"
    return usernames


def loadPostUrls(urls_filename, comments_eq_or_more):
    eq_more = int(comments_eq_or_more)
    with open(urls_filename) as f:
        for line in f:
            num, url = line.split()
            num = int(num)
            if num < eq_more:
                continue
            else:
                yield url


def open_utf8(path, mode):
    try:
        f = codecs.open(path, mode, encoding='utf-8')
    except IOError as e:
        print "\n\n\nerror occured %s\n\n\n" % path
        print e.message
    else:
        return f


### lan ###
import re
misc_pattern = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    r"\`\~\!\@\#\$\%\^\&\*\(\)\-\_\=\+\\\|\"\'\[\{\]\}\,\<\.\>\/\?\;\:"
    "\s"  # white space
    "]+", flags=re.UNICODE)
kor = re.compile(u'[ㄱ-ㅋ가-힣]')
eng = re.compile(u'[a-zA-z]')  # NOT used yet
addressed_username = re.compile(u'@([a-z0-9._@]+)')
regset = {"kor": kor, "eng": eng}


def getCommentLan(text):
    text = addressed_username.sub("", text)
    text = misc_pattern.sub("", text)
    kor_len, kor_ratio = getLenAndRatio(text, "kor")
    if (kor_len > 5 and kor_ratio > 0.5) or kor_len > 15:
        return lantype.KOR_GUESS
    return lantype.NON_KOR_GUESS


# return KOR, NON_KOR or UNKNOWN
def getCapsLan(caps):
    whole_text = ""
    for text in caps:
        if type(text) not in (unicode,):
            continue
        text = misc_pattern.sub("", text)
        whole_text += text

    kor_len, kor_ratio = getLenAndRatio(whole_text, "kor")

    if kor_ratio is None:
        return lantype.UNKNOWN, kor_len, kor_ratio

    if (kor_len > 10 and kor_ratio > 0.3):  # or kor_len > 30:
        return lantype.KOR, kor_len, kor_ratio
    elif kor_len < 5 or kor_ratio < 0.15:
        return lantype.NON_KOR, kor_len, kor_ratio
    else:
        return lantype.UNKNOWN, kor_len, kor_ratio


def getLenAndRatio(text, lan):  # to be changed
    try:
        lan_reg = regset[lan]
    except KeyError:
        print "language regex key error!!"
        return
    total_len = 0
    lan_count = 0
    text = misc_pattern.sub("", text)
    total_len += len(text)
    lan_count += len(lan_reg.findall(text))

    if total_len == 0:
        return 0, None
    return lan_count, (float(lan_count)/total_len)

### json_helper ###
def searchAll(d_json, target):
    result = []

    if type(d_json) == dict:
        for key in d_json:
            result += searchAll(d_json[key], target)
            if key == target:
                # print "Found %s!" % target
                result.append(d_json[key])

    elif type(d_json) == list:
        for item in d_json:
            result += searchAll(item, target)

    return result


def searchAllNested(d_json, target):
    target_ls = target.split(' ')
    result = [d_json]

    for i in range(len(target_ls)):
        cur_target = target_ls[i]
        new_result = []

        if not result:
            return []
        for sub_d_json in result:
            new_result += searchAll(sub_d_json, cur_target)

        result = new_result

    return result


def trim(string):
    head = string.find('{')
    tail = -string[::-1].find('}')
    return string[head:tail]


def extractJson(response, token):
    ls = response.xpath('//*[@type="text/javascript"]')
    for item in ls:
        text_ls = item.xpath('./text()').extract()
        if not text_ls:
            continue
        if token in text_ls[0][:100]:
            text = text_ls[0]
            break
    return trim(text)


def decodeJsonInResponse(response):
    return json.loads(extractJson(response, "window._sharedData"))
