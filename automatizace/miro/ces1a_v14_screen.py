#!/usr/bin/env python3
"""Miro v13 live semantic screening for approved candidate catalog. READ-ONLY.
Approved candidate wordings are analyst-generated, NOT board source data.
Do not emit any board item text, IDs, or other untrusted client content.
"""
import os,json,hashlib,collections,html,re,unicodedata,urllib.request,urllib.parse,urllib.error,sys,time,difflib,math
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
SOURCE_SHA="26f142048d8aeda0cb2ce6d4fa31d1aa45b236cfc41d08a1ef1badb139421486"
DATA=[["EV01","Zdravotně pojistný plán VZP pro daný rok byl schválen Poslaneckou sněmovnou."],["EV02","Hospodaření VZP pro nový rok přešlo do zákonného provizoria."],["EV03","VZP vznikla závazná povinnost odstranit závažné nedostatky zjištěné dohledovým orgánem."],["EV04","Pro významnou skupinu zdravotních služeb nabyla účinnosti nová úhradová pravidla."],["EV05","Pro definovanou skupinu pojištěnců se změnil právní rozsah hrazených zdravotních služeb."],["EV06","Pojištěncům z vymezené skupiny se nově zpřístupnil významný příspěvek z fondu prevence."],["EV07","Pojištěncům v nedostatečně pokrytém území se stala reálně dostupnou potřebná hrazená péče."],["EV08","Nový způsob hrazené péče se stal běžně dostupným širší skupině pojištěnců."],["EV09","VZP byla doručena platná přihláška pojištěnce ke změně zdravotní pojišťovny."],["EV10","Neoprávněná přeregistrace pojištěnce k jiné zdravotní pojišťovně byla zrušena."],["EV11","Smlouva zabezpečující nedostatkovou zdravotní péči ve významné oblasti nabyla účinnosti."],["EV12","Oprávnění poskytovatele pro podstatnou část jeho smluvně zajištěné péče zaniklo."],["EV13","Bylo potvrzeno neoprávněné vykázání zdravotních služeb s významným dopadem na úhrady."],["EV14","Pravomocně skončilo významné přezkumné řízení změnou původního rozhodnutí VZP vůči pojištěnci."],["EV15","Pojištěnci vznikl nebo zanikl nárok na hrazenou péči v ČR podle pravidel evropské koordinace."],["EV16","Pro zdravotní pojišťovny byla závazně stanovena nová výše přerozdělovaných prostředků za rozhodné období."],["EV17","VZP vznikla nová účinná zákonná povinnost poskytovat veřejné správě významný okruh dat."],["EV18","Oprávněným institucím nebo veřejnosti byla zpřístupněna nová významná datová služba VZP."],["EV19","Účetní závěrka VZP za uplynulý rok byla schválena Poslaneckou sněmovnou."],["EV20","VZP přestala ve významném rozsahu včas hradit splatné úhrady za zdravotní péči."],["EV21","VZP obnovila včasné hrazení významného objemu splatných úhrad za zdravotní péči."],["EV22","VZP ztratila kritickou odbornou kapacitu potřebnou pro výkon významné zákonné agendy."],["EV23","VZP obnovila kritickou odbornou kapacitu pro výkon významné zákonné agendy."],["EV24","Významná digitální služba VZP se stala nedostupnou pojištěncům, plátcům nebo poskytovatelům."],["EV25","Poskytování významné digitální služby VZP uživatelům bylo obnoveno."],["EV26","Smlouva zajišťující strategicky důležitou činnost VZP nabyla účinnosti."],["EV27","Smluvní zajištění strategicky důležité činnosti VZP skončilo."],["EV28","Pravomocné rozhodnutí soudu nebo orgánu veřejné moci podstatně změnilo práva či závazky VZP."],["EV29","Klienti v podstatné části území ztratili funkční možnost uskutečnit nezastupitelné právně významné podání vůči VZP."],["EV30","Klientům byla obnovena možnost uskutečnit právně významná podání vůči VZP."],["EV31","Ve VZP bylo potvrzeno významné porušení zabezpečení osobních údajů."],["EV32","Dotčeným fyzickým osobám bylo oznámeno závažné porušení zabezpečení jejich osobních údajů."],["EV33","V důsledku bezpečnostního incidentu ztratila VZP důvěryhodnou dostupnost významné evidence potřebné pro plnění zákonných povinností."]]
def call(path,par=None):
    url=ROOT+"/"+path
    if par:url+="?"+urllib.parse.urlencode(par)
    for i in range(5):
        try:
            request=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
            with urllib.request.urlopen(request,timeout=40) as result:return json.load(result)
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and i<4:time.sleep(min(12,2**i+1));continue
            raise RuntimeError("HTTP "+str(e.code)) from None
def pages(path,q=None):
    out=[];cursor=None
    for _ in range(80):
        par=dict(q or {},limit=50)
        if cursor:par["cursor"]=cursor
        p=call(path,par);out+=p.get("data",[])
        cursor=p.get("cursor")
        if not cursor:return out
    raise RuntimeError("pagination incomplete")
def text(x):return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str((x.get("data") or {}).get("content") or "")))).strip()
def norm(s):
    s="".join(c for c in unicodedata.normalize("NFKD",s.lower()) if not unicodedata.combining(c))
    s=re.sub(r"\b(?:ev|n)\d{2}\b"," ",s)
    return re.sub(r"[^a-z0-9 ]"," ",s).strip()
STOP=set("vzp byla bylo byli pro nova nove novy vznikla vznikl ze za se je pri podle jejich jeho roku danou od do na nad pod z v k s i a o c jako proti nebo ktera ktere vyznamne vyznamny".split())
def words(s):return set(w for w in norm(s).split() if len(w)>3 and w not in STOP)
def scoring(a,b):
    a=norm(a);b=norm(b)
    ta=words(a);tb=words(b)
    j=len(ta&tb)/max(1,len(ta|tb))
    seq=difflib.SequenceMatcher(None,a,b).ratio()
    return .63*j+.37*seq, j,seq
def main():
    frames=pages("items",{"type":"frame"})
    f=[x for x in frames if hashlib.sha256(str(x.get("id")).encode()).hexdigest()==SOURCE_SHA]
    if len(f)!=1:raise RuntimeError("unique v13 frame absent")
    items=pages("items",{"parent_item_id":f[0]["id"]})
    notes=[x for x in items if x.get("type")=="sticky_note"]
    if len(notes)!=116:raise RuntimeError("source drift: unexpected events count")
    existing=[text(x) for x in notes]
    exact=0;flagged=0
    for key,label in DATA:
        pairs=sorted([(scoring(label,old),i) for i,old in enumerate(existing)],reverse=True,key=lambda z:z[0][0])[:3]
        sc=pairs[0][0][0]
        status="EXACT" if norm(label)==norm(existing[pairs[0][1]]) else "HIGH_SIMILARITY" if sc>=.62 else "REVIEW" if sc>=.42 else "NO_LEXICAL_MATCH"
        if status=="EXACT":exact+=1
        if status in ("EXACT","HIGH_SIMILARITY","REVIEW"):flagged+=1
        ranked=" ".join("%d:%.2f"%(i+1,p[0][0]) for p,i in pairs)
        print("SCREEN",key,status,"TOP_SCORES",ranked,flush=True)
    print("SOURCE_LIVE_PASS","events",len(notes),"candidates",len(DATA),"exact",exact,"flagged",flagged)
    print("AUDIT_ONLY_NO_WRITES")
if __name__=="__main__":
    try:main()
    except Exception as e:print("AUDIT_FAIL",type(e).__name__,str(e));sys.exit(1)
