
# -*- coding:utf-8 -*-
import sys

import socket
socket.setdefaulttimeout(20)

import sublime, sublime_plugin
import time, os, re
import json

try:
    from urllib import urlopen, urlencode
    reload(sys)   
    sys.setdefaultencoding('utf8')
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import urlencode

pattern = re.compile(r'fmz@([a-zA-Z0-9]{32})')

token_region = 'fmz_token'
__version__ = '0.0.2'
buf_cache = {}

def getToken(view):
    syntax = view.settings().get("syntax")
    if 'JavaScript' not in syntax and 'Python' not in syntax and 'C++' not in syntax and 'Text' not in syntax and 'Pine' not in syntax:
        return (None, None)
    view.erase_regions(token_region)
    content = view.substr(sublime.Region(0, view.size()))
    pos = view.find("^[ \t]*(//|#)\s*fmz@[a-zA-Z0-9]{32}[ \t]*$", 0)
    if pos:
        match = pattern.search(view.substr(pos))
        if not match:
            sublime.error_message("Invalid sync token !")
        else:
            view.add_regions(token_region, [pos], 'keyword', 'dot', sublime.HIDDEN)
            view.set_status("quant", "sync plugin loaded")
            content, number = re.subn("(//|#)\s*fmz@[a-zA-Z0-9]{32}\s*",'',content)
            return (match.group(1), content)

    
    view.erase_status("fmz")
    return (None, None)

def SyncFile(filename, token, content):
    success = False
    errCode = 0
    rsync_url = "https://www.fmz.com/rsync"
    if token[0] == 'n':
        rsync_url = "https://www.youquant.com/rsync"
        name = 'YouQuant'
    sublime.status_message(name + " is Sync changed ....")
    msg = ""
    try:
        data = {'token': token, 'method':'push', 'content': content, 'version': __version__, 'client': 'sublime ' + sublime.version()}
        resp = json.loads(urlopen(rsync_url, urlencode(data).encode('utf8')).read().decode('utf8'))
        errCode = resp["code"]
        if errCode < 100:
            success = True
            msg = 'Hi ' + resp['user'] + ", sync success !\n\n[" + filename + "] saved to [" + resp['name'] + "]"
            sublime.status_message(msg)
            sublime.message_dialog(msg)
        else:
            if errCode == 405:
                msg = 'Sorry, ' + resp['user'] + ", sync failed !\n\nRenew the token of [" + resp['name'] + "]"
            elif errCode == 406:
                msg = 'plugin for sublime need update !'
            else:
                msg = "sync [" + filename + " ] failed, errCode: %d\n\nMay be the token is not correct !" % errCode
            
    except:
        msg = str(sys.exc_info()[1]) + "\n\sync failed, please retry again !"

    if not success:
        sublime.status_message(msg)
        sublime.error_message(msg)
    return success

class SaveOnModifiedListener(sublime_plugin.EventListener):
    def on_load(self, view):
        self.token = ''
        if getToken(view):
            sublime.status_message("sync plugin ready .")

    def on_post_save(self, view):
        token, content = getToken(view)
        if not token:
            return
        rawContent = view.substr(sublime.Region(0, view.size()))
        if buf_cache.get(token) == rawContent:
            sublime.error_message("sync abort because file not changed !")
            return

        file_name = os.path.basename(view.file_name())
        if SyncFile(file_name, token, content):
            buf_cache[token] = rawContent
