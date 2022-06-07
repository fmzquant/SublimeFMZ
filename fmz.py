" Vim sync plugin for FMZ
"

if !exists("g:fmz_async")
    let g:fmz_async = 0
endif

function! ShortEcho(msg)
  " regular :echomsg is supposed to shorten long messages when shortmess+=T but it does not.
  " under "norm echomsg", echomsg does shorten long messages.
  let saved=&shortmess
  set shortmess+=T
  exe "norm :echomsg a:msg\n"
  let &shortmess=saved
endfunction

function! SyncFMZ()
PyForFMZ << EOF
import vim
import sys

import socket
socket.setdefaulttimeout(20)

import time, os, re
import json
from threading import Thread

try:
    from urllib import urlopen, urlencode
    reload(sys)   
    sys.setdefaultencoding('utf8')
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import urlencode
__version__ = '0.0.2'

def SyncFile(filename, token, content):
    success = False
    errCode = 0
    msg = ""
    try:
        rsync_url = "https://www.fmz.%s/rsync" % ("cn" if token[0] == 'n' else "com", )
        data = {'token': token, 'method':'push', 'content': content, 'version': __version__, 'client': 'vim'}
        resp = json.loads(urlopen(rsync_url, urlencode(data).encode('utf8')).read().decode('utf8'))
        errCode = resp["code"]
        if errCode < 100:
            success = True
            msg = 'Hi ' + resp['user'] + ", [" + filename + "] saved to [" + resp['name'] + "]"
        else:
            if errCode == 405:
                msg = 'Sorry, ' + resp['user'] + ", sync failed ! Renew the token of [" + resp['name'] + "]"
            elif errCode == 406:
                msg = 'FMZ plugin need update ! http://www.fmz.com'
            else:
                msg = "FMZ sync [" + filename + " ] failed, errCode: %d, May be the token is not correct !" % errCode
            
    except:
        msg = str(sys.exc_info()[1]) + ", FMZ sync failed, please retry again !"
    vim.command('call ShortEcho("' + msg.replace('"', '\"') +'")')
    return success

cur_buf = vim.current.buffer
pattern = re.compile(r'fmz@([a-zA-Z0-9]{32})')
content = []
token = None
for line in cur_buf:
	skip = False
	if not token:
		match = pattern.search(line)
		if match:
			token = match.group(1)
			skip = True
	content.append(line if not skip else '')
if token:
    if vim.eval('g:fmz_async').strip() == '1':
        thread = Thread(target=SyncFile,
                        args=(vim.eval('bufname("%")'), token, '\n'.join(content)))
        thread.setDaemon(True)
        thread.start()
    else:
        SyncFile(vim.eval('bufname("%")'), token, '\n'.join(content))
EOF

endfunction

if has('python3')
  command! -nargs=* PyForFMZ python3 <args>
elseif has('python')
  command! -nargs=* PyForFMZ python <args>
endif

autocmd BufWritePost *.js :call SyncFMZ()
autocmd BufWritePost *.py :call SyncFMZ()
autocmd BufWritePost *.cpp :call SyncFMZ()
autocmd BufWritePost *.txt :call SyncFMZ()
autocmd BufWritePost *.pine :call SyncFMZ()
autocmd BufWritePost *.tv :call SyncFMZ()

