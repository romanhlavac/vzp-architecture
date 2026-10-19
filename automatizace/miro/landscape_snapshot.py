#!/usr/bin/env python3
"""Read-only paginated inventory with recipient-encrypted evidence. No client data in logs."""
import json,os,sys,time,urllib.request,urllib.parse,urllib.error,subprocess,pathlib,hashlib
BASE='https://api.miro.com/v2/boards/'+urllib.parse.quote(os.environ['MIRO_DIAGNOSTIC_BOARD_ID'],safe='')
TOKEN=os.environ['MIRO_DIAGNOSTIC_TOKEN']
def request(path,params=None):
 u=(path if path.startswith('https://') else BASE+'/'+path)
 if params:u+='?'+urllib.parse.urlencode(params)
 for n in range(5):
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/json'}),timeout=40) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code in (429,500,502,503,504) and n<4:time.sleep(min(20,2**n+1));continue
   raise RuntimeError('Read failed HTTP '+str(e.code)) from None
  except Exception:
   if n<2:time.sleep(2);continue
   raise RuntimeError('Read transport failed') from None
def listing(path):
 out=[];cursor=None
 for _ in range(400):
  q={'limit':50}
  if cursor:q['cursor']=cursor
  obj=request(path,q);out+=obj.get('data',[]);cursor=obj.get('cursor')
  if not cursor:return out
 raise RuntimeError('Pagination incomplete')
def main():
 ctx=request('https://api.miro.com/v1/oauth-token')
 scope=ctx.get('scopes',ctx.get('scope',[]))
 if isinstance(scope,str):scope=scope.replace(',',' ').split()
 if not {'boards:read','boards:write'}<=set(scope):raise RuntimeError('Required OAuth scopes absent')
 board=request('')
 def ident(v):return str(v.get('id','')) if isinstance(v,dict) else str(v or '')
 if ident(ctx.get('team') or ctx.get('team_id'))!=ident(board.get('team') or board.get('team_id')):raise RuntimeError('OAuth team mismatch')
 data={'items':listing('items'),'connectors':listing('connectors'),'timestamp':time.time(),'oauth_scopes_verified':True}
 plain=json.dumps(data,ensure_ascii=False).encode()
 pathlib.Path('encrypted-evidence').mkdir(exist_ok=True)
 cmd=['openssl','cms','-encrypt','-binary','-aes-256-cbc','-outform','DER','-out','encrypted-evidence/snapshot.p7m','automatizace/miro/landscape_recipient.pem']
 p=subprocess.run(cmd,input=plain,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if p.returncode:raise RuntimeError('Evidence encryption failed')
 print('READ_ONLY PASS; items=%d connectors=%d sha256=%s'%(len(data['items']),len(data['connectors']),hashlib.sha256(plain).hexdigest()))
if __name__=='__main__':
 try:main()
 except Exception as e:print('FAIL:',str(e));sys.exit(1)
