# -*- coding: utf-8 -*-

import json

def searchAll(d_json, target):
    result = []
    if type(d_json) == dict:
        for key in d_json:
            result += searchAll(d_json[key], target)
            if key == target:
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
