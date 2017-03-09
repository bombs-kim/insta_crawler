#!/usr/bin/env python
# -*- coding: utf8 -*-


import jsonlib
import re


def load_json(json_str, as_utf8=True):
  '''Build object from json string using jsonlib'''

  try:
    json_obj = jsonlib.read(json_str)
  except jsonlib.ReadError as e:
    json_obj = jsonlib.read(_remove_invalid_escape(json_str))

  # if as_utf8 is true, convert unicode string in json_obj to utf8
  if as_utf8: _encode_utf8(json_obj)

  return json_obj

def dump_json(json_obj, is_utf8=True, ind=None):
  '''Build json string from json object using jsonlib'''

  # if is_utf8 is true, convert utf8 string in json_obj to unicode
  if is_utf8: _decode_utf8(json_obj)

  return jsonlib.write(json_obj, ascii_only=False, indent=ind)


def _remove_invalid_escape(text):

  text = text.replace('\b', '')

  while True:
    #m = re.search(r'[^\\](\\)[^\\"/bfnrtu]', text)
    m = re.search(r'[^\\](?:\\\\)*(\\)[^\\"/bfnrtu]', text)
    if not m or not m.groups():
      break
    text = text[:m.start(1)]+'\\\\'+text[m.end(1):]

  return text


def _encode_utf8(obj):
  '''Encode unicode strings in a json object as utf8'''

  if type(obj) == dict:
    for i, v in obj.iteritems():
      if type(v) == unicode: obj[i] = v.encode('utf8')
      else:                  _encode_utf8(v)
  elif type(obj) == list:
    for i, v in enumerate(obj):
      if type(v) == unicode: obj[i] = v.encode('utf8')
      else:                  _encode_utf8(v)

def _decode_utf8(obj):
  '''Decode utf8 strings in a json object as unicode'''

  if type(obj) == dict:
    for i, v in obj.iteritems():
      if type(v) == str: obj[i] = v.decode('utf8')
      else:              _decode_utf8(v)
  elif type(obj) == list:
    for i, v in enumerate(obj):
      if type(v) == str: obj[i] = v.decode('utf8')
      else:              _decode_utf8(v)


def _stopWatch(in_path, out_path, utf8):

  with open(in_path) as in_file:

    if out_path: out_file = open(out_path, 'w')

    start_time = time.time()

    for line in in_file:
      obj = load_json(line, utf8)
      if out_path: out_file.write(dump_json(obj, utf8)+'\n')
      else:        dump_json(obj, utf8)

    sys.stdout.write('utf8_flag(%s) : %.2f\n' % (str(utf8), time.time()-start_time))

    if out_path: out_file.close()


if __name__ == '__main__':

  import sys
  reload(sys)
  sys.setdefaultencoding('utf8')

  import time

  if len(sys.argv) != 2:
    sys.stderr.write('usage: %s test_json_file\n' % sys.argv[0])
    sys.exit(1)

  _stopWatch(sys.argv[1], "ll_uni", False)
  _stopWatch(sys.argv[1], "ll_utf8", True)
