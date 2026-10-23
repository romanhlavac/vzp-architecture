#!/usr/bin/env python3
"""Read-only preflight; identifiers and geometry only in logs, never board card text."""
import os,json,urllib.request,urllib.parse,urllib.error,time,hashlib
B=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"]
assert B=="uXjVHiylz-0="
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(B,safe="")+"/"
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
def api(verb,path,body=None):
    req=urllib.request.Request(BASE+path,method=verb,data=json.dumps(body).encode() if body is not None else None,headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
    for n in range(4 if verb=="GET" else 1):
        try:
            with urllib.request.urlopen(req,timeout=55) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if verb=="GET" and e.code in (429,500,502,503,504) and n<3: time.sleep(2**n);continue
            raise RuntimeError("REST_"+str(e.code)) from None
def page(path,filters=None):
    out=[];q=dict(filters or {},limit=50)
    for _ in range(200):
        z=api("GET",path+"?"+urllib.parse.urlencode(q));out+=z.get("data",[])
        c=z.get("cursor") or z.get("nextCursor")
        if not c:return out
        q["cursor"]=c
    raise RuntimeError("PAGINATION")
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":")).encode()).hexdigest()

PROTECTED=["3458764687741774534","3458764687757375873"]
def stable(o):
    return {k:o.get(k) for k in ("id","type","data","style","geometry","position","parent","startItem","endItem","captions","shape")}
def snapshot(fid,links):
    f=api("GET","frames/"+fid);kids=page("items",{"parent_item_id":fid});ids={o["id"] for o in kids}
    edges=[o for o in links if (o.get("startItem") or {}).get("id") in ids or (o.get("endItem") or {}).get("id") in ids]
    return {"frame":stable(f),"kids":{o["id"]:stable(o) for o in kids},"edges":{o["id"]:stable(o) for o in edges}}

import html,re
CHAIN=[('3458764687949068244','01'),('3458764688162404596','02'),('3458764687939229431','03a'),('3458764687939229785','03b'),('3458764688202201527','03c'),('3458764687939406397','03d'),('3458764687949762980','03e'),('3458764687942876552','04'),('clusters','05'),('3458764687938964779','06'),('boundary','07')]
REF='3458764688162124320'
SCENARIOS=[('SC-01','3458764687939229431','H1 hlavní rozhodovací tok • H3 výjimky • H6 matching pravidla','Výsledek: jednoznačná reference nebo přiznaná nejednoznačnost.','Zkoumá hranici rozhodnutí o identitě; shoda a výjimka mohou mít odlišná pravidla.'),('SC-02','3458764687939229785','H2 lifecycle a opravy • H3 konflikty • H5 autorita a consistency','Výsledek: doložená referenční změna se zachovanou historií.','Zkoumá provenienci, retroaktivitu a odpovědnost za referenční záznam.'),('SC-05','3458764688202201527','H4 externí handoff • H5 autorita, synchronizace a consistency','Výsledek: posouzený externí podnět a jeho referenční dopad.','Ověřuje rozdíl mezi autoritou zdroje a rozhodnutím uvnitř domény; přenos je OPEN.'),('SC-03','3458764687939406397','H4 předání z agendy • H6 jiný jazyk, pravidla a change drivers','Výsledek: referenční projekce již doloženého agendového rozhodnutí.','Ověřuje, kde končí rozhodnutí agendy a začíná odpovědnost za projekci.'),('SC-04','3458764687949762980','H2 vznik/změna/zánik • H3 opravy • H4 předání odpovědnosti','Výsledek: doložená platnost zastupování a jeho historie.','Testuje odlišný lifecycle a opravy; samostatná L2 z toho automaticky neplyne.')]
def name(f):return (f.get('data') or {}).get('title','')
def norm(s):return ' '.join(html.unescape(re.sub('<[^>]*>',' ',str(s))).split())
def link(fid):return 'https://miro.com/app/board/'+B+'/?moveToWidget='+fid
def position(f):return f['position']['x'],f['position']['y']
def rect(f):
 x,y=position(f);w=f['geometry']['width'];h=f['geometry']['height'];return x-w/2,y-h/2,x+w/2,y+h/2

def ensure_frame(title,x,y,w,h):
 fs=page('items',{'type':'frame'});found=[f for f in fs if name(f)==title]
 assert len(found)<2,'DUPLICATE_FRAME'
 if found:
  f=found[0]
  assert abs(f['geometry']['width']-w)<1 and abs(f['geometry']['height']-h)<1,'FRAME_SIZE_DRIFT'
  return f
 return api('POST','frames',{'data':{'title':title},'position':{'x':x,'y':y,'origin':'center'},'geometry':{'width':w,'height':h},'style':{'fillColor':'#ffffff'}})
def card(f,key,text,x,y,w,h,fill='#f1f5f9',font=78):
 kids=page('items',{'parent_item_id':f['id']})
 body='<p><strong>'+html.escape(key)+'</strong></p><p>'+text.replace('\n','</p><p>')+'</p>'
 found=[k for k in kids if norm((k.get('data') or {}).get('content','')).startswith(key)]
 assert len(found)<2,'DUPLICATE_CARD'
 payload={'data':{'content':body,'shape':'rectangle'},'position':{'x':x,'y':y,'origin':'center'},'geometry':{'width':w,'height':h},'style':{'fillColor':fill,'color':'#172b4d','fontSize':str(font),'fontFamily':'open_sans','textAlign':'left','textAlignVertical':'middle','borderColor':'#cbd5e1','borderWidth':'2'}}
 if found:
  obj=found[0];api('PATCH','shapes/'+obj['id'],payload)
 else:
  payload['parent']={'id':f['id']};obj=api('POST','shapes',payload)
 read=api('GET','shapes/'+obj['id']);assert norm(read['data']['content'])==norm(body),'CARD_READBACK'
 assert read.get('parent',{}).get('id')==f['id'],'CARD_PARENT'
 return read

def move(fid,x,y,title=None):
 links=page('connectors');before=snapshot(fid,links);f=before['frame'];payload={'position':{'x':x,'y':y,'origin':'center'}}
 if title:payload['data']={'title':title}
 if abs(f['position']['x']-x)>1 or abs(f['position']['y']-y)>1 or (title and f['data']['title']!=title):api('PATCH','frames/'+fid,payload)
 after=snapshot(fid,page('connectors'))
 for k in ('id','type','style','geometry','parent'):assert after['frame'].get(k)==f.get(k),'FRAME_DRIFT_'+k
 if not title:assert after['frame']['data']==f['data'],'FRAME_DATA_DRIFT'
 assert abs(after['frame']['position']['x']-x)<1 and abs(after['frame']['position']['y']-y)<1,'POSITION_DRIFT'
 assert before['kids']==after['kids'],'CHILD_DRIFT_'+fid
 assert before['edges']==after['edges'],'EDGE_DRIFT_'+fid
 print('MOVE_PASS',fid,len(after['kids']),len(after['edges']),x,y,flush=True)
 return after['frame']

def plan(frames):
 fm={f['id']:f for f in frames};left=225638;out=[]
 for fid,step in CHAIN:
  if fid=='clusters':w,h=7600,6500
  elif fid=='boundary':w,h=7600,6500
  else:w,h=fm[fid]['geometry']['width'],fm[fid]['geometry']['height']
  out.append((fid,step,left+w/2,26000+h/2,w,h));left+=w+1100
 return out

def annotations(f,kind):
 if kind=='clusters':
  card(f,'05 · EVIDENCE → ODPOVĚDNOSTI','DEMO / WORKING • čtyři skupiny důkazů, nikoli čtyři hotové subdomény.',3800,450,7100,600,'#dbeff0',92)
  data=[('A · Rozhodnutí o identitě','SC-01: matching, nejednoznačnost, merge/split. Rozlišující pravidla a invarianty.'),('B · Referenční změna a historie','SC-02 + SC-05: provenance, zdrojová autorita, opravy a časová konzistence.'),('C · Projekce agendové role','SC-03: rozhodnutí vzniká v agendě; reference eviduje doložený výsledek.'),('D · Zastupování a platnost','SC-04: vlastní lifecycle, doklady a opravy; odlišnost od role je otázka k validaci.')]
  for i,(k,t) in enumerate(data):card(f,k,t,3800,1450+1050*i,7100,900,font=82)
  card(f,'Syntéza → kandidáti','A+B podporují S0.1; C+D podporují S0.2. Sdílené scénáře a M:N vazby zůstávají.\nSPLIT / MERGE / SHIFT = OPEN. Zdroj/systém není automaticky L2.',3800,5820,7100,1000,'#fff2cb',80)
 else:
  card(f,'07 · BOUNDARY RATIONALE → 1C','DEMO / CANDIDATE / OPEN • žádná validovaná business hranice.',3800,450,7100,600,'#dbeff0',92)
  card(f,'S0.1 · Proč vzniká kandidát','SC-01/02/05 sdílejí odpovědnost za referenční identitu, autoritu a historii.\nIN: reference a její pravidla. OUT: rozhodování o agendových právech.\nAlternativa: oddělit matching od změn/historie; potřeba ověřit pravidla a consistency.',3800,1700,7100,1600,font=82)
  card(f,'S0.2 · Proč vzniká kandidát','SC-03/04 sdílejí evidenci již doložené role/vztahu a jeho platnosti.\nIN: referenční projekce. OUT: vznik, změna či zánik agendového práva.\nAlternativa: oddělit zastupování od rolí; ověřit jazyk, lifecycle a change drivers.',3800,3450,7100,1600,font=82)
  card(f,'OPEN · Co musí rozhodnout 1C','KEEP / MERGE / SEPARATE / SHIFT / KEEP_OPEN.\nPorovnat protipříklady, autority záznamů, konzistenci a předání; doplnit vlastníka rozhodnutí.\nMetodické DEMO: business reviewer/owner a sign-off nejsou doloženy.',3800,5200,7100,1600,'#ffdee0',82)

def main():
 mode=os.environ.get('STORY_MODE','audit');assert mode in ('audit','apply','verify')
 fs=page('items',{'type':'frame'});fm={f['id']:f for f in fs};p=plan(fs)
 for fid,step,x,y,w,h in p:print('PLAN',fid,step,x,y,w,h,flush=True)
 if mode=='audit':print('AUDIT_PASS_WRITES_0',flush=True);return
 before_ids=set(fm);links=page('connectors');protected={i:snapshot(i,links) for i in PROTECTED}
 targets={fid for fid,*_ in p if fid.isdigit()}|{REF}
 untouched={i:stable(f) for i,f in fm.items() if i not in targets}
 if mode=='apply':
  for fid,step,x,y,w,h in p:
   if fid.isdigit():
    old=name(fm[fid]);prefix='MAIN · 1B.'+step+' · '
    move(fid,x,y,old if old.startswith(prefix) else prefix+old)
  move(REF,322000,29435,'REFERENCE · Process Modelling · historická notace')
  for fid,step,x,y,w,h in p:
   if not fid.isdigit():
    f=ensure_frame('CES DEMO · 1B.'+step+' · '+('Evidence clustering' if fid=='clusters' else 'Boundary rationale / 1C'),x,y,w,h)
    annotations(f,fid);print('NEW_FRAME',fid,f['id'],flush=True)
  # Five choice cards aligned immediately below the scenario models.
  scp={fid:(x,y,w,h) for fid,step,x,y,w,h in p}
  for sc,fid,why,outcome,reason in SCENARIOS:
   x,y,w,h=scp[fid];f=ensure_frame('CES DEMO · '+sc+' · Proč tento scénář',x,35250,w,2500)
   card(f,sc+' · PROČ TENTO SCÉNÁŘ',why+'\n'+outcome+'\n'+reason+'\nWORKING / DEMO • <a href="'+link(fid)+'">Otevřít scénář</a>',w/2,1250,w-400,2100,font=94)
   print('WHY_FRAME',sc,f['id'],flush=True)
  # Native navigation/selection supplement: explicitly covers all five scenarios.
  f=ensure_frame('CES DEMO · 1B · Čtecí trasa a coverage',228438,31000,5600,3900)
  rows=[' → '.join('<a href="'+link(fid)+'">'+sc+'</a>' for sc,fid,*_ in SCENARIOS),'H1 hlavní tok • H2 lifecycle • H3 výjimky • H4 handoff • H5 autorita/consistency • H6 jazyk/change drivers','Pět reprezentativních scénářů. Původní čtyřscénářový inventář je doplněn o SC-05. Nejde o úplné procesní pokrytí.','Iterace: hypotézy ↔ scénáře ↔ evidence ↔ L2 ↔ 1C. Pořadí čtení není povinný algoritmus.']
  card(f,'1B · MAIN · METODICKÉ DEMO','\n'.join(rows),2800,1950,5100,3400,'#dbeff0',100)
  print('NAV_FRAME',f['id'],flush=True)
  # Step bands; no fictitious target models.
  for title,y,body in [('KROK 1 · 1B · MAIN',24000,'Vstup: 1A nad tímto pásmem. Čtěte zleva doprava: výběr → metoda → scénáře → syntéza → evidence → kandidátní L2 → 1C. DEMO; není target návrhem VZP.'),('KROK 1 · 1C · PLANNED',41000,'Boundary Validation • dosud nerealizováno v této hlavní trase. Vstupem jsou kandidáti a OPEN z 1B.'),('KROK 2 · PLANNED',46000,'Strategická klasifikace stejných subdomén. Dosud nerealizováno.'),('KROK 3 · PLANNED',51000,'Bounded Contexts / Context Map / ownership a Roadmap v0. Dosud nerealizováno.'),('KROK 4 · PLANNED',56000,'Návrh a ověření cílové architektury. Dosud nerealizováno; nativní model dle metodiky v Archi.'),('KROK 5 · PLANNED',61000,'Přechod SIS → CIS a Roadmap. Dosud nerealizováno; nejde o nasazení či převzetí.')]:
   f=ensure_frame('CES DEMO · '+title,232000,y,12700,2200)
   card(f,title,body,6350,1100,12000,1800,'#dbeff0',120);print('LANE_FRAME',f['id'],flush=True)
  f=ensure_frame('REFERENCE / ARCHIVE · mimo hlavní trasu',322000,24000,8000,2200)
  card(f,'REFERENCE / ARCHIVE','Historické ukázky a původní verze jsou zachovány. Nejsou aktuálním výstupem kroků 1C–5. Hlavní metodický průchod je vlevo.',4000,1100,7400,1800,'#e2e8f0',105)
 fs2=page('items',{'type':'frame'});fm2={f['id']:f for f in fs2};assert before_ids<=set(fm2),'LOST_FRAME'
 assert untouched=={i:stable(fm2[i]) for i in untouched},'UNRELATED_FRAME_CHANGED'
 assert protected=={i:snapshot(i,page('connectors')) for i in PROTECTED},'PROTECTED_CHANGED'
 for fid,step,x,y,w,h in p:
  if fid.isdigit():assert abs(fm2[fid]['position']['x']-x)<1 and abs(fm2[fid]['position']['y']-y)<1,'FINAL_POSITION'
 print('G1_G2_PASS_ORIGINAL_IDS_CONTENT_CONNECTORS_PROTECTED','original',len(before_ids),'after',len(fm2),'G4_OPEN',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print('STOP',type(e).__name__,str(e),flush=True);raise SystemExit(1)
