#!/usr/bin/env python3
"""Additive versioned domain landscape. Public controller holds only generic rules and hashes.
Source/template/other content is read-only. All private evidence encrypted before upload.
"""
import json,os,sys,time,re,html,hashlib,pathlib,subprocess,urllib.request,urllib.parse,urllib.error,math
from landscape_snapshot import listing,request as get
ROOT=pathlib.Path(__file__).parent
RULES=json.loads((ROOT/'landscape_rules.json').read_text())
MODE=os.environ.get('LANDSCAPE_MODE','audit')
TITLE='CES-1A · L1 DOMAIN LANDSCAPE · v2 (BP ES v12 mapping)'
BOARD=os.environ['MIRO_DIAGNOSTIC_BOARD_ID'];TOKEN=os.environ['MIRO_DIAGNOSTIC_TOKEN']
BASE='https://api.miro.com/v2/boards/'+urllib.parse.quote(BOARD,safe='')+'/'
def ident(x):return str(x.get('id',''))
def parent(x):return str((x.get('parent') or {}).get('id',''))
def tx(x):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str((x.get('data') or {}).get('content',''))))).strip()
def h(x):return hashlib.sha256(x.encode()).hexdigest()
def digest(x):return h(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')))
def semantic(x):return {k:x[k] for k in ('id','type','data','style','geometry','position','parent','startItem','endItem','shape','captions') if k in x}
def px(x):return float((x.get('position') or {}).get('x',0))
def py(x):return float((x.get('position') or {}).get('y',0))
def size(x,k):return float((x.get('geometry') or {}).get(k,0))
def edge(x,k):return str((x.get(k) or {}).get('id',''))
def snapshot():return {'items':listing('items'),'connectors':listing('connectors')}
def encrypt(data):
 out=pathlib.Path('encrypted-evidence');out.mkdir(exist_ok=True)
 p=subprocess.run(['openssl','cms','-encrypt','-binary','-aes-256-cbc','-outform','DER','-out',str(out/'landscape.p7m'),str(ROOT/'landscape_recipient.pem')],input=json.dumps(data,ensure_ascii=False).encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if p.returncode:raise RuntimeError('Evidence encryption failed')
def mutate(path,payload):
 # POST is deliberately NOT replayed after uncertain transport response.
 # A subsequent audit inventories objects before idempotent resume.
 raw=json.dumps(payload,ensure_ascii=False).encode()
 req=urllib.request.Request(BASE+path,data=raw,headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/json','Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  encrypt({'failure':{'path':path,'status':e.code,'body':e.read().decode('utf-8','replace'),'payload':payload}})
  raise RuntimeError('POST '+path+' HTTP '+str(e.code)+'; encrypted diagnostic; audit before resume') from None
 except Exception:raise RuntimeError('POST transport uncertain; audit before resume') from None

def build_plan(before):
 frames=[z for z in before['items'] if z['type']=='frame']
 def select(key):
  a=[z for z in frames if h(ident(z))==RULES[key]]
  if len(a)!=1:raise RuntimeError('Source frame identity mismatch')
  return a[0]
 source=select('source_frame_id_hash');template=select('template_frame_id_hash')
 sc=[z for z in before['items'] if parent(z)==ident(source)]
 tc=[z for z in before['items'] if parent(z)==ident(template)]
 notes=sorted([z for z in sc if z['type']=='sticky_note'],key=lambda z:(py(z),px(z)))
 byhash={h(tx(z)):z for z in notes};idx={ident(z):i+1 for i,z in enumerate(notes)}
 if len(notes)!=RULES['expected_source_events'] or len(byhash)!=len(notes):raise RuntimeError('Event inventory mismatch')
 expected=[v for g in RULES['groups'].values() for v in g]
 if len(expected)!=len(set(expected)) or set(expected)!=set(byhash):raise RuntimeError('One-primary mapping mismatch')
 dom={}
 for z in tc:
  m=re.match(r'(A[123]|S0|B[1-9]|C1|D[1-6])\s*·',tx(z))
  if z['type']=='shape' and m and 'Aktéři' in tx(z):
   if m.group(1) in dom:raise RuntimeError('Ambiguous domain')
   dom[m.group(1)]=z
 if sorted(dom,key=lambda c:py(dom[c]))!=RULES['codes']:raise RuntimeError('Domain skeleton/order mismatch')
 links=[z for z in before['connectors'] if edge(z,'startItem') in idx and edge(z,'endItem') in idx]
 if len(links)!=RULES['expected_edges']:raise RuntimeError('Edge inventory mismatch')
 protected=[semantic(x) for x in [source,template]+sc+tc+links]
 if digest(protected)!=RULES['protected_source_digest']:raise RuntimeError('Source/template changed; reconcile before write')
 domain_of={ident(byhash[k]):c for c,vals in RULES['groups'].items() for k in vals}
 rows={};y=450
 for c in RULES['codes']:
  count=len(RULES['groups'][c]);height=max(700,math.ceil(count/6)*340+130)
  if c in ('S0','B1','B2','B3','B6','B8','B9'):height=max(height,1000)
  rows[c]={'top':y,'height':height,'count':count};y+=height+60
 fw=11000;fh=max(y+450,750+len(links)*340)
 return {'source':source,'template':template,'notes':notes,'byhash':byhash,'index':idx,'domains':dom,'links':links,'domain_of':domain_of,'rows':rows,'width':fw,'height':fh,'frames':frames}

class Builder:
 def __init__(self,before,plan):
  self.before=before;self.p=plan;self.items=[];self.mapping={};self.links=[];self.created=[]
  targets=[f for f in plan['frames'] if (f.get('data') or {}).get('title')==TITLE]
  if len(targets)>1:raise RuntimeError('Duplicate target frame; recovery required')
  self.frame=targets[0] if targets else None
  if self.frame:self.items=[z for z in before['items'] if parent(z)==ident(self.frame)]
 def frame_create(self):
  if self.frame:return
  right=max(px(f)+size(f,'width')/2 for f in self.p['frames'])
  self.frame=mutate('frames',{'data':{'title':TITLE},'style':{'fillColor':'#ffffff'},'geometry':{'width':self.p['width'],'height':self.p['height']},'position':{'x':right+1600+self.p['width']/2,'y':1300+self.p['height']/2,'origin':'center'}})
  self.created.append(ident(self.frame))
 def create(self,typ,key,x,y,w,content,height=None,style=None,data=None):
  same=[z for z in self.items if z['type']==typ and tx(z)==re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',content))).strip() and abs(px(z)-x)<2 and abs(py(z)-y)<2]
  if len(same)>1:raise RuntimeError('Duplicate deterministic object')
  if same:return same[0]
  # Prevent blindly overwriting or duplicating a manually changed slot.
  conflicts=[z for z in self.items if z['type']==typ and abs(px(z)-x)<2 and abs(py(z)-y)<2]
  if conflicts:raise RuntimeError('Target slot drift; manual reconciliation required')
  payload={'data':dict(data or {},content=content),'position':{'x':x,'y':y,'origin':'center'},'geometry':{'width':w},'parent':{'id':ident(self.frame)}}
  if typ=='shape':payload['data'].setdefault('shape','rectangle');payload['geometry']['height']=height
  if typ=='sticky_note':payload['data'].setdefault('shape','rectangle')
  if style:payload['style']=style
  paths={'shape':'shapes','text':'texts','sticky_note':'sticky_notes'}
  z=mutate(paths[typ],payload);self.items.append(z);self.created.append(ident(z));return z
 def text(self,key,x,y,w,c,font=20):return self.create('text',key,x,y,w,c,style={'fontFamily':'open_sans','fontSize':str(font),'color':'#26353a','textAlign':'left'})
 def headers(self):
  self.text('title',3400,100,6500,'<strong>L1 DOMAIN LANDSCAPE · v2 / BP ES v12</strong>',52)
  self.text('subtitle',3400,210,6500,'DEMO · pracovní DDD hypotézy k business validaci · 20 L1 oblastí / 110 primárních událostí / 46 dohledatelných P/D vazeb',25)
  self.text('legend',3400,320,6500,'Oranžová = původní business událost (právě jednou). E001–E110 = referenční index. Šedá reference vpravo není další událost. Pořadí kartiček samo o sobě nevyjadřuje proces.',22)
  self.text('relations',8750,110,4100,'<strong>46 P/D VAZEB · REFERENČNÍ ZOOM</strong>',34)
  self.text('rellegend',8750,250,4100,'P = věcný předpoklad · D = podmíněný možný důsledek. Původní label a podmínka jsou zachovány. Křivka není API call ani automatická reakce. Reference odkazují na jedinou primární událost vlevo.',22)
 def domain(self,c):
  row=self.p['rows'][c];top=row['top'];height=row['height'];original=self.p['domains'][c]
  r=RULES['rationales'][c];ns=[self.p['byhash'][k] for k in RULES['groups'][c]]
  ex='; '.join(tx(x) for x in ns[:2]) if ns else 'Žádná událost BP v12; jde o mezeru pokrytí tohoto vstupu.'
  add='<p><strong>PROČ TYTO UDÁLOSTI PATŘÍ SEM / CES HRANICE</strong></p>'
  for label,text in [('Výsledek',r[0]),('Pravidla / cyklus / autorita',r[1]),('Vazba na CES',r[2]),('Zařazení – příklady',ex),('Vyloučení / sousedé',r[3])]:add+='<p><strong>'+label+':</strong> '+html.escape(text)+'</p>'
  add+='<p><strong>BP v12: '+str(len(ns))+' primárních událostí · PROPOSED / OPEN</strong></p>'
  # Preserve original text and all earlier rationale, as a single domain-owned description.
  content=original['data']['content']+add
  st=dict(original['style']);st.update({'fontSize':'18','textAlign':'left','textAlignVertical':'top'})
  self.create('shape','domain-'+c,1000,top+height/2,1800,content,height,st)
  self.create('shape','lane-'+c,4300,top+height/2,4400,'',height,{'fillColor':st.get('fillColor','#f2f2f2'),'fillOpacity':'0.35','borderColor':st.get('borderColor','#aeb6ba'),'borderWidth':'1','borderOpacity':'1','borderStyle':'normal'})
  if not ns:self.text('empty-'+c,4200,top+130,3900,'0 událostí ve zdroji BP ES v12. Doména je zachována; doplnění discovery je OPEN.',24)
  for n,obj in enumerate(ns):
   num=self.p['index'][ident(obj)];x=2393.5+(n%6)*700;y=top+170+(n//6)*340
   new=self.create('sticky_note','event-'+str(num),x,y,387,obj['data']['content'],style={k:v for k,v in obj.get('style',{}).items() if k in ('fillColor','textAlign','textAlignVertical')},data={'shape':'rectangle'})
   self.mapping[ident(obj)]={'newID':ident(new),'code':c,'eventKey':'E%03d'%num,'text':tx(obj),'x':x,'y':y}
   url='https://miro.com/app/board/'+BOARD+'/?moveToWidget='+ident(obj)
   self.text('index-'+str(num),x,y+152,387,'<a href="'+url+'">E%03d · %s · zdroj BP v12</a>'%(num,c),16)
 def reference(self,obj,x,y):
  sid=ident(obj);num=self.p['index'][sid];c=self.p['domain_of'][sid]
  target=self.mapping.get(sid)
  if not target:raise RuntimeError('Primary target missing')
  url='https://miro.com/app/board/'+BOARD+'/?moveToWidget='+target['newID']
  text='<p><strong>REFERENCE E%03d · %s</strong></p><p><a href="%s">%s</a></p>'%(num,c,url,html.escape(tx(obj)))
  return self.create('shape','reference',x,y,650,text,200,{'fillColor':'#f2f2f2','fillOpacity':'1','borderColor':'#aeb6ba','borderWidth':'1','borderOpacity':'1','borderStyle':'normal','fontFamily':'open_sans','fontSize':'20','color':'#26353a','textAlign':'center','textAlignVertical':'middle'})
 def relation(self,i,edgeobj):
  ids={ident(n):n for n in self.p['notes']};a=edge(edgeobj,'startItem');b=edge(edgeobj,'endItem');y=620+i*340
  left=self.reference(ids[a],7350,y);right=self.reference(ids[b],10350,y)
  codea=self.p['domain_of'][a];codeb=self.p['domain_of'][b]
  label='R%02d · %s → %s · %s'%(i+1,codea,codeb,'CROSS-DOMAIN' if codea!=codeb else 'INTRA-DOMAIN')
  url='https://miro.com/app/board/'+BOARD+'/?moveToWidget='+ident(edgeobj)
  self.text('rhead',8800,y-142,3900,'<a href="'+url+'">'+label+'</a>',19)
  existing=[z for z in self.before['connectors']+self.links if edge(z,'startItem')==ident(left) and edge(z,'endItem')==ident(right)]
  if len(existing)>1:raise RuntimeError('Duplicate native edge')
  if existing:link=existing[0]
  else:
   st={k:v for k,v in edgeobj.get('style',{}).items() if k in ('startStrokeCap','endStrokeCap','strokeWidth','strokeStyle','strokeColor','color','textOrientation','fontSize')};st['fontSize']='20';st['textOrientation']='horizontal'
   link=mutate('connectors',{'startItem':{'id':ident(left),'snapTo':'right'},'endItem':{'id':ident(right),'snapTo':'left'},'shape':'curved','style':st,'captions':edgeobj.get('captions',[])})
   self.links.append(link);self.created.append(ident(link))
  return {'sourceEdgeID':ident(edgeobj),'sourceEventID':a,'targetEventID':b,'newSourcePrimaryID':self.mapping[a]['newID'],'newTargetPrimaryID':self.mapping[b]['newID'],'newSourceReferenceID':ident(left),'newTargetReferenceID':ident(right),'newConnectorID':ident(link),'sourceDomain':codea,'targetDomain':codeb,'captions':edgeobj.get('captions',[]),'status':'PRESERVED / BUSINESS CONDITION TO VALIDATE'}
 def execute(self):
  self.frame_create();self.headers()
  cs=['S0'] if MODE=='pilot' else RULES['codes']
  for c in cs:self.domain(c)
  edges=[]
  for i,e in enumerate(self.p['links']):
   if MODE=='pilot' and not (self.p['domain_of'][edge(e,'startItem')]=='S0' and self.p['domain_of'][edge(e,'endItem')]=='S0'):continue
   edges.append(self.relation(i,e))
   if MODE=='pilot':break
  return edges

def main():
 if MODE not in ('audit','pilot','apply'):raise RuntimeError('Invalid mode')
 before=snapshot();plan=build_plan(before)
 print('PREFLIGHT PASS: events=110 edges=46 domains=20 source/template hashes match')
 b=Builder(before,plan)
 if MODE=='audit':
  encrypt({'snapshot':before,'mode':MODE,'targetFrame':b.frame,'sourceTemplateVerified':True})
  print('AUDIT ONLY: no mutations');return
 edges=b.execute();after=snapshot()
 targetid=ident(b.frame);targetchildren={ident(z) for z in after['items'] if parent(z)==targetid}
 old={ident(x):semantic(x) for x in before['items']+before['connectors'] if ident(x)!=targetid and parent(x)!=targetid and not(edge(x,'startItem') in {ident(v) for v in b.items} or edge(x,'endItem') in {ident(v) for v in b.items})}
 aft={ident(x):semantic(x) for x in after['items']+after['connectors']}
 if any(aft.get(k)!=v for k,v in old.items()):raise RuntimeError('Unrelated/source invariant failed')
 items=[x for x in after['items'] if parent(x)==targetid];notes=[x for x in items if x['type']=='sticky_note'];cons=[x for x in after['connectors'] if edge(x,'startItem') in targetchildren and edge(x,'endItem') in targetchildren]
 expected=19 if MODE=='pilot' else 110;ec=1 if MODE=='pilot' else 46
 if len(notes)!=expected or len(cons)!=ec:raise RuntimeError('Target counts mismatch')
 for sid,m in b.mapping.items():
  z=next((x for x in notes if ident(x)==m['newID']),None)
  if not z or tx(z)!=m['text'] or abs(px(z)-m['x'])>2 or abs(py(z)-m['y'])>2:raise RuntimeError('Event text/position mismatch')
 for e in edges:
  z=next(x for x in cons if ident(x)==e['newConnectorID'])
  if z.get('shape')!='curved' or z.get('captions')!=e['captions']:raise RuntimeError('Edge semantics/readback mismatch')
 encrypt({'mode':MODE,'targetFrame':b.frame,'events':b.mapping,'edges':edges,'snapshot':after,'createdIDs':b.created,'protectedItemsVerified':len(old),'sourceTemplateVerified':True})
 print('STRUCTURAL PASS: primary=%d native_curved=%d protected=%d created=%d'%(len(notes),len(cons),len(old),len(b.created)))
 print('VISUAL ACCEPTANCE OPEN: requires actual native canvas review')
if __name__=='__main__':
 try:main()
 except Exception as e:print('FAIL:',str(e));sys.exit(1)
