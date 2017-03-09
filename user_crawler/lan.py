#! -*- coding: utf-8 -*-
import lantype
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
def getCapsLanAndInfo(caps, bio, lan):
    whole_text = ""
    for text in caps:
        if type(text) not in (unicode,):
            continue
        text = misc_pattern.sub("", text)
        whole_text += text

    kor_len, kor_ratio = getLenAndRatio(whole_text, lan)

    # if bio seems Korean, immediately return KOR
    if bio is not None:
        bio_kor_len, bio_kor_ratio = getLenAndRatio(bio, lan)
        if bio_kor_len > 5 and bio_kor_ratio > 0.5:
            return lantype.KOR, kor_len, kor_ratio

    # 해쉬태그에 대해서는 따로 조사?

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
