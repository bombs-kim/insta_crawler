#! -*- coding: utf-8 -*-

from urlparse import urljoin
import json
import lantype

"""
def loadKorUser(user, user_dict):
    entry = dict(
            user_id=user["user_id"],
            username=user["username"],
            last_post_id=user["last_post_id"],
            user_freq=user["user_freq"],
            last_crawled_date=user.get("last_crawled_date", 0),
            code=user.get("code", "")
        )
    # if an entry with the same username exists,
    # it automatically overwrite on that entry
    user_dict[user["user_id"]] = entry
"""


def loadKorUsers(path):
    user_dict = {}
    filename = "total-users.jl"
    try:
        with open(urljoin(path, filename)) as f:
            for line in f:
                user = json.loads(line)
                user_dict[user["user_id"]] = user
                # loadKorUser(user, user_dict)
    except IOError:
        print "KOR user file doesn't exist"
    return user_dict


def saveKorUsers(path, d):
    import codecs
    filename = "total-users.jl"
    try:
        with codecs.open(urljoin(path, filename), 'w', encoding='utf-8') as f:
            for key in d:
                json.dump(d[key], f)
                f.write('\n')
    except IOError:
        print "Error in saving KOR users"


def loadOtherUsers(path):
    kor_guess_path = path + 'kor-guess.txt'
    non_kor_guess_path = path + 'non-kor-guess.txt'
    # unknown_path = path + 'unknown.txt'
    try:
        open(kor_guess_path, 'a').close()
        open(non_kor_guess_path, 'a').close()
        # open(unknown_path, 'a').close()

        with open(kor_guess_path) as kg_f, open(non_kor_guess_path) as nkg_f:
                # open(unknown_path) as uk_f:
            d = {}
            for f, lan_t in [(kg_f, lantype.KOR_GUESS),
                             (nkg_f, lantype.NON_KOR_GUESS)]:
                             # (uk_f, lantype.UNKNOWN)]:
                for line in f:
                    user_id, username = line[:-1].split('\t')
                    d[user_id] = [lan_t, username]
            return d
    except IOError as e:
        print "IOError in loading other users %s" % e.strerror
        return {}


def saveNonKorUsers(path, d):
    non_kor_path = path + 'non-kor.txt'
    try:
        with open(non_kor_path, 'a') as f:
            for key in d:
                if d[key][0] == lantype.NON_KOR:
                    f.write(key)
                    f.write('\n')
    except IOError:
        print "IOError in saving NON_KOR users"


def saveOtherUsers(path, d):
    kor_guess_path = path + 'kor-guess.txt'
    non_kor_guess_path = path + 'non-kor-guess.txt'
    # unknown_path = path + 'unknown.txt'
    try:
        with open(kor_guess_path, 'w') as kg_f,\
         open(non_kor_guess_path, 'w') as nkg_f:
         # open(unknown_path, 'w') as uk_f:
            for key in d:
                if d[key][0] == lantype.KOR_GUESS:
                    kg_f.write(key+'\t')  # user_id
                    kg_f.write(d[key][1]) # username
                    kg_f.write('\n')
                if d[key][0] == lantype.NON_KOR_GUESS:
                    nkg_f.write(key+'\t')  # user_id
                    nkg_f.write(d[key][1]) # username
                    nkg_f.write('\n')
                # if d[key][0] == lantype.UNKNOWN:
                #    uk_f.write(key+'\t')  # user_id
                #    uk_f.write(d[key][1]) # username
                #    uk_f.write('\n')
    except IOError:
        print "IOError in saving other users"
