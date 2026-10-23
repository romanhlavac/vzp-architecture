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
# One-time READ ONLY metadata inventory for CES DEMO 1B narrative reconciliation.
# No contents of business cards or live board objects are written to CI logs.
import collections,re
audit_items=data['boards'].get(os.environ['MIRO_DIAGNOSTIC_BOARD_ID'],{}).get('items') or []
audit_edges=data['boards'].get(os.environ['MIRO_DIAGNOSTIC_BOARD_ID'],{}).get('connectors') or []
frames=[z for z in audit_items if z.get('type')=='frame']
parented=collections.defaultdict(list)
for z in audit_items:
 parentid=str((z.get('parent') or {}).get('id') or '')
 if parentid:parented[parentid].append(z)
print('CES_FRAME_METADATA_START',len(frames),flush=True)
for f in sorted(frames,key=lambda z:(float((z.get('position') or {}).get('y') or 0),float((z.get('position') or {}).get('x') or 0))):
 title=str((f.get('data') or {}).get('title') or '')
 if not re.search(r'CES|DEMO|1B|1C|Subdomain|Process|E2E|Method|Metod',title,re.I):continue
 fid=str(f.get('id'));kids=parented.get(fid,[])
 counts=collections.Counter(str(k.get('type')) for k in kids)
 signals=collections.Counter()
 for o in kids:
  col=str((o.get('style') or {}).get('fillColor') or '').lower()
  if col=='#e5a6cd':signals['system_pink']+=1
  if col=='#72d5ed':signals['command_cyan']+=1
  if col=='#bb8dcc':signals['policy_violet']+=1
  if col=='#c8e99b':signals['query_green']+=1
  if str(o.get('type'))=='sticky_note' and col=='red':signals['hotspot_red']+=1
 ids={str(o.get('id')) for o in kids}
 conn=sum(str((e.get('startItem') or {}).get('id')) in ids and str((e.get('endItem') or {}).get('id')) in ids for e in audit_edges)
 pos=f.get('position') or {};geo=f.get('geometry') or {}
 row={'frame':fid,'title':title,'x':round(float(pos.get('x') or 0)),
      'y':round(float(pos.get('y') or 0)),'width':round(float(geo.get('width') or 0)),
      'height':round(float(geo.get('height') or 0)),
      'items':len(kids),'types':dict(counts),'signals':dict(signals),'native_links':conn}
 print('CES_FRAME_META',json.dumps(row,ensure_ascii=False,separators=(',',':')),flush=True)
print('CES_FRAME_METADATA_END',flush=True)

pathlib.Path('encrypted-evidence').mkdir(exist_ok=True)
p=subprocess.run(['openssl','cms','-encrypt','-binary','-aes-256-cbc','-outform','DER','-out','encrypted-evidence/continuation.p7m','automatizace/miro/landscape_recipient.pem'],input=json.dumps(data,ensure_ascii=False).encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert p.returncode==0
print('ENCRYPTED_EVIDENCE_READY')
