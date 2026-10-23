#!/usr/bin/env python3
"""Bounded read-only continuation evidence. Encrypt all board contents to recipient."""
import os,json,urllib.request,urllib.parse,urllib.error,time,subprocess,pathlib
TOKEN=os.environ['MIRO_DIAGNOSTIC_TOKEN']
def get(board,path,params=None):
 url='https://api.miro.com/v2/boards/'+urllib.parse.quote(board,safe='')+'/'+path
 if params:url+='?'+urllib.parse.urlencode(params)
 for n in range(4):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+TOKEN}),timeout=45) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code in (429,500,502,503,504) and n<3:time.sleep(2**n);continue
   raise RuntimeError('HTTP_'+str(e.code)) from None
def listing(b,path,params=None):
 out=[];cursor=None
 for _ in range(150):
  q=dict(params or {},limit=50)
  if cursor:q['cursor']=cursor
  r=get(b,path,q);out+=r.get('data',[]);cursor=r.get('cursor')
  if not cursor:return out
 raise RuntimeError('PAGINATION')
data={'timestamp':time.time(),'boards':{}}
for b in [os.environ['MIRO_DIAGNOSTIC_BOARD_ID'],'uXjVH27wYU4=']:
 try:
  data['boards'][b]={'items':listing(b,'items'),'connectors':listing(b,'connectors')}
  print('BOARD_READ_PASS',len(data['boards'][b]['items']),len(data['boards'][b]['connectors']),flush=True)
 except RuntimeError as e:
  data['boards'][b]={'error':str(e)};print('BOARD_READ_FAILED',str(e),flush=True)
pathlib.Path('encrypted-evidence').mkdir(exist_ok=True)
p=subprocess.run(['openssl','cms','-encrypt','-binary','-aes-256-cbc','-outform','DER','-out','encrypted-evidence/continuation.p7m','automatizace/miro/landscape_recipient.pem'],input=json.dumps(data,ensure_ascii=False).encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert p.returncode==0
print('ENCRYPTED_EVIDENCE_READY')
