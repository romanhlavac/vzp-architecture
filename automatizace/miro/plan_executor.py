#!/usr/bin/env python3
"""Guarded native diagram plan; business payload is recipient-encrypted at rest."""
import os,json,base64,pathlib,tempfile,subprocess,urllib.request,urllib.parse,urllib.error,time,hashlib,html,re,sys
P=pathlib.Path('automatizace/miro');OUT=pathlib.Path('encrypted-evidence');OUT.mkdir(exist_ok=True)
TOKEN=os.environ['MIRO_DIAGNOSTIC_TOKEN'];B=os.environ['MIRO_DIAGNOSTIC_BOARD_ID']
ROOT='https://api.miro.com/v2/boards/'+urllib.parse.quote(B,safe='')+'/'
def call(method,path,body=None):
 data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
 for attempt in range(4 if method=='GET' else 1):
  try:
   q=urllib.request.Request(ROOT+path,data=data,headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json','Accept':'application/json'},method=method)
   with urllib.request.urlopen(q,timeout=50) as r:
    raw=r.read();return json.loads(raw) if raw else {}
  except urllib.error.HTTPError as e:
   if method=='GET' and e.code in (429,500,502,503,504) and attempt<3:time.sleep(2**attempt);continue
   evidence['http_error_body']=e.read().decode(errors='replace')[:8000]
   raise RuntimeError('HTTP_'+str(e.code)+'_'+method+'_'+path.split('?')[0]) from None
def listing(path,params=None):
 out=[];cursor=None
 for _ in range(150):
  q=dict(params or {},limit=50)
  if cursor:q['cursor']=cursor
  d=call('GET',path+'?'+urllib.parse.urlencode(q));out+=d.get('data',[]);cursor=d.get('cursor')
  if not cursor:return out
 raise RuntimeError('PAGINATION')
def sem(z):return {k:z[k] for k in ('id','type','data','style','geometry','position','parent','startItem','endItem','shape','captions') if k in z}
def digest(z):return hashlib.sha256(json.dumps(sem(z),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def tx(z):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',z.get('data',{}).get('content','')))).strip()
def snapshot(ids):
 frames=listing('items',{'type':'frame'});wanted={x['id']:x for x in frames if x['id'] in ids}
 if set(wanted)!=set(ids):raise RuntimeError('FRAME_MISSING')
 items=list(wanted.values())
 for f in ids:items+=listing('items',{'parent_item_id':f})
 itemids={z['id'] for z in items}
 cons=[z for z in listing('connectors') if z.get('startItem',{}).get('id') in itemids or z.get('endItem',{}).get('id') in itemids]
 return {'items':items,'connectors':cons,'timestamp':time.time()}
evidence={'map':{},'edges':[],'created':[],'updated':[],'deleted':[]}
def save():
 subprocess.run(['openssl','cms','-encrypt','-binary','-aes-256-cbc','-outform','DER','-out',str(OUT/'plan-result.p7m'),str(P/'landscape_recipient.pem')],input=json.dumps(evidence,ensure_ascii=False).encode(),check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def main():
 pack=json.loads((P/'plan_payload.json').read_text())
 with tempfile.TemporaryDirectory() as td:
  td=pathlib.Path(td);(td/'wrapped').write_bytes(base64.b64decode(pack['wrapped_private']));(td/'payload').write_bytes(base64.b64decode(pack['payload']))
  subprocess.run(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-iter','200000','-pass','env:MIRO_DIAGNOSTIC_TOKEN','-in',str(td/'wrapped'),'-out',str(td/'key')],check=True,stderr=subprocess.DEVNULL)
  subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-in',str(td/'payload'),'-inkey',str(td/'key'),'-out',str(td/'plan')],check=True,stderr=subprocess.DEVNULL)
  plan=json.loads((td/'plan').read_text())
 if plan['board']!=B:raise RuntimeError('BOARD_MISMATCH')
 allowed=set(x['id'] for x in plan['frames']);protected=set(plan['protected_frames'])
 if allowed&protected:raise RuntimeError('PROTECTED_FRAME_IN_PLAN')
 before=snapshot(list(allowed|protected));evidence['before']=before
 allb={z['id']:z for z in before['items']+before['connectors']}
 if os.environ.get('PLAN_EXECUTION','audit')!='apply':
  for k,h in plan.get('audit_guards',{}).items():
   if k not in allb or digest(allb[k])!=h:raise RuntimeError('AUDIT_DRIFT_'+k)
  evidence['status']='READ_ONLY_AUDIT_PASS';evidence['guard_count']=len(plan.get('audit_guards',{}));print('READ_ONLY_AUDIT_PASS',evidence['guard_count'],flush=True);return
 if plan.get('resume_desired'):
  for n in plan['nodes']:
   z=allb.get(n['old']);assert z and tx(z)==re.sub(r'\s+',' ',n['text']).strip(),'RESUME_TEXT'
   assert z.get('parent',{}).get('id')==n['frame'],'RESUME_PARENT'
   assert abs(z['position']['x']-n['x'])<1 and abs(z['position']['y']-n['y'])<1,'RESUME_POSITION'
  for f in plan['frames']:
   z=allb[f['id']];assert abs(z['position']['x']-f['x'])<1 and abs(z['position']['y']-f['y'])<1,'RESUME_FRAME'
 for k,h in plan['guards'].items():
  if k not in allb or digest(allb[k])!=h:raise RuntimeError('FRESH_GUARD_DRIFT_'+k)
 print('FRESH_GUARDS_PASS',len(plan['guards']),flush=True)
 if os.environ.get('PLAN_EXECUTION','audit')!='apply':
  print('READ_ONLY_AUDIT_PASS',len(plan['nodes']),len(plan['edges']),flush=True);return
 for f in plan['frames']:
  call('PATCH','frames/'+f['id'],{'data':{'title':f['title']},'position':{'x':f['x'],'y':f['y'],'origin':'center'},'geometry':{'width':f['width'],'height':f['height']}})
  evidence['updated'].append(f['id'])
 for n in plan['nodes']:
  endpoint='sticky_notes' if n['type']=='sticky_note' else 'shapes'
  body={'data':{'content':n['content'],'shape':'rectangle'},'position':{'x':n['x'],'y':n['y'],'origin':'center'},'geometry':{'width':n['width']},'parent':{'id':n['frame']}}
  if endpoint=='sticky_notes':body['style']={'fillColor':n['fill'],'textAlign':'center','textAlignVertical':'middle'}
  else:
   body['geometry']['height']=n['height'];body['style']={'fillColor':n['fill'],'fontFamily':'open_sans','fontSize':str(n['font']),'textAlign':'center','textAlignVertical':'middle','color':'#26353a','borderWidth':'1','borderColor':n['fill']}
  if n.get('old'):
   obj=call('PATCH',endpoint+'/'+n['old'],body);wid=n['old'];evidence['updated'].append(wid)
  else:
   obj=call('POST',endpoint,body);wid=obj['id'];evidence['created'].append(wid)
  evidence['map'][n['key']]=wid
  if len(evidence['map'])%10==0:print('NODES_WRITTEN',len(evidence['map']),flush=True)
 for e in plan['edges']:
  body={'startItem':{'id':evidence['map'][e['from']],'snapTo':e['source_side']},'endItem':{'id':evidence['map'][e['to']],'snapTo':e['target_side']},'shape':'curved','style':{'strokeColor':'#26353a','strokeWidth':'2','fontSize':'24','startStrokeCap':'none','endStrokeCap':'stealth'}}
  if e['label']:body['captions']=[{'content':html.escape(e['label']),'position':'50%','textAlignVertical':'middle'}]
  obj=call('PATCH' if e.get('old') else 'POST','connectors/'+e['old'] if e.get('old') else 'connectors',body);evidence['edges'].append(obj['id']);evidence['updated' if e.get('old') else 'created'].append(obj['id'])
 for d in sorted(plan['delete'],key=lambda d:0 if d['type']=='connector' else 1):
  if d['id'] not in allb:raise RuntimeError('DELETE_OUTSIDE_BASELINE')
  endpoint={'connector':'connectors','sticky_note':'sticky_notes','shape':'shapes','text':'texts'}[d['type']]
  call('DELETE',endpoint+'/'+d['id']);evidence['deleted'].append(d['id'])
 after=snapshot(list(allowed|protected));evidence['after']=after
 amap={z['id']:z for z in after['items']+after['connectors']}
 for n in plan['nodes']:
  z=amap.get(evidence['map'][n['key']]);assert z and tx(z)==re.sub(r'\s+',' ',n['text']).strip(),'TEXT_READBACK'
  assert z.get('parent',{}).get('id')==n['frame'],'PARENT_READBACK'
  assert abs(z['position']['x']-n['x'])<1 and abs(z['position']['y']-n['y'])<1,'POSITION_READBACK'
 for e,mid in zip(plan['edges'],evidence['edges']):
  z=amap[mid];assert z['startItem']['id']==evidence['map'][e['from']] and z['endItem']['id']==evidence['map'][e['to']],'EDGE_READBACK'
 protids={z['id'] for z in before['items'] if z['id'] in protected or z.get('parent',{}).get('id') in protected}
 protectedobjects=[z for z in before['items']+before['connectors'] if z['id'] in protids or z.get('startItem',{}).get('id') in protids or z.get('endItem',{}).get('id') in protids]
 assert all(z['id'] in amap and digest(z)==digest(amap[z['id']]) for z in protectedobjects),'PROTECTED_DRIFT'
 evidence['status']='NATIVE_READBACK_PASS';evidence['protected_count']=len(protectedobjects)
 print('NATIVE_READBACK_PASS',len(plan['nodes']),len(plan['edges']),'PROTECTED',len(protectedobjects),'VISUAL_PENDING',flush=True)
try:
 main()
except Exception as e:
 evidence['error']=type(e).__name__+': '+str(e);print('PLAN_STOP',type(e).__name__,str(e),flush=True);sys.exit(2)
finally:save()
