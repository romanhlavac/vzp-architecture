#!/usr/bin/env python3
"""READ-ONLY encrypted baseline capture for an architectural Miro comparison.

No plaintext board text, board IDs, frame IDs, OAuth tokens, or item IDs in
GitHub source, logs, cache or artifacts. Session-specific public key only.
"""
import os,sys,json,re,time,urllib.parse,urllib.request,urllib.error
import tempfile,subprocess,gzip,base64,secrets,hashlib
TOKEN=os.getenv("MIRO_DIAGNOSTIC_TOKEN","").strip()
BOARD=os.getenv("MIRO_DIAGNOSTIC_BOARD_ID","").strip()
if not TOKEN or not BOARD:sys.exit("FAIL: missing authorized runtime secrets")
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")
PUBKEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwckqoaElCuY7ahq9VTqr\nY90JC6TJX8wR7TPCDb80ZMroYFalhEKBbYwGJNk3X+0PePq2PN9EDRmbN1boCjRj\ng3/Nwqq9wAyugHrQQAnajruQIfPR7/eE3YVIngkPuyoMZUDL8jc1huACVPwRdvwJ\nJK/UoiIdRYs21ik1bQRl2EellIV+F6mHYqyrNh0lAmeBP3tgqQ5zU/JK6W3qZ2cv\n7RhTmt8N/qxhfdcroDefMfN3KSunM5Y7AdhLz9IF2b3JZ3OSjUrjg3EHJWWMYa5A\nnMmYO4tAXlXrfrUsiloiKAq+7dTBBI44A4Tq5QMnlZGDWgadnAwJEl1ujuxvy2je\nPQIDAQAB\n-----END PUBLIC KEY-----\n"
def api(path,params=None):
    url=ROOT+"/"+path
    if params:url+="?"+urllib.parse.urlencode(params)
    for n in range(4):
        try:
            q=urllib.request.Request(url,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
            with urllib.request.urlopen(q,timeout=35) as ans:return json.loads(ans.read())
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and n<3:
                time.sleep(2**n+1);continue
            raise RuntimeError("API read failed HTTP "+str(e.code)) from None
def listall(path,params=None):
    ans=[];cursor=None
    for n in range(80):
        q=dict(params or {});q["limit"]=50
        if cursor:q["cursor"]=cursor
        v=api(path,q);ans+=v.get("data",[])
        cursor=v.get("cursor")
        if not cursor:return ans
    raise RuntimeError("pagination guard")
def pos(x):return x.get("position") or {}
def box(x):return x.get("geometry") or {}
def clean(x):
    return {
      "id":str(x.get("id","")),"type":x.get("type"),"data":x.get("data") or {},
      "position":pos(x),"geometry":box(x),"style":x.get("style") or {},
      "parent":(x.get("parent") or {}).get("id"),
      "locked":x.get("isSupported") if "isSupported" in x else None
    }
def detail(x):
    routes={"sticky_note":"sticky_notes","shape":"shapes","text":"texts","card":"cards","frame":"frames"}
    if x.get("type") in routes:
        try:return api(routes[x["type"]]+"/"+str(x["id"]))
        except Exception:return x
    return x
def main():
    frames=listall("items",{"type":"frame"})
    found=[]
    for f in frames:
        g=detail(f);raw=json.dumps(g.get("data") or {},ensure_ascii=False)
        title=g.get("data",{}).get("title") or g.get("title") or ""
        title=title or raw[:170]
        if re.search(r"CES|1A|L1|DOM|EVENT|BP",str(title),re.I):
            found.append((f,g,str(title)))
    # Supplement known geometric live frame even if its title isn't exposed in the collection.
    for f in frames:
        wh=box(f)
        if 16000<float(wh.get("width") or 0)<19000 and 9800<float(wh.get("height") or 0)<11000:
            if all(z[0]["id"]!=f["id"] for z in found):found.append((f,detail(f),"geometric-candidate"))
    found=found[:20]
    allcon=listall("connectors")
    result={"frames_index":[{"id":str(f["id"]),"title":t,"geometry":box(f),"position":pos(f)} for f,g,t in found],
            "selected_frames":[],"captured_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    # Capture at most six most relevant frames by title / recency, incl L1 source and generated Work frame.
    selected=sorted(found,key=lambda z:(0 if re.search("DOMAIN|LANDSCAPE|L1",z[2],re.I) else 1,0 if re.search("v2|V12|v12",z[2],re.I) else 1))[:7]
    for f,ff,title in selected:
        fid=str(f["id"])
        items=listall("items",{"parent_item_id":fid})
        kids=[clean(detail(x)) for x in items]
        ids={z["id"] for z in kids}
        links=[]
        for conn in allcon:
            sa=str((conn.get("startItem") or {}).get("id") or "")
            sb=str((conn.get("endItem") or {}).get("id") or "")
            if sa in ids or sb in ids:
                links.append(conn)
        result["selected_frames"].append({"frame":clean(ff),"title":title,"items":kids,"connectors":links})
    raw=json.dumps(result,ensure_ascii=False,separators=(",",":")).encode()
    if len(raw)>900000:raise RuntimeError("capture exceeds safety limit")
    with tempfile.TemporaryDirectory() as tmp:
        pem=tmp+"/public.pem";keyfile=tmp+"/secretpass";blob=tmp+"/snapshot.bin";enc=tmp+"/encrypted.bin"
        open(pem,"w").write(PUBKEY)
        password=secrets.token_urlsafe(32)
        open(keyfile,"w").write(password)
        open(blob,"wb").write(gzip.compress(raw,compresslevel=9))
        subprocess.run(["openssl","enc","-aes-256-cbc","-pbkdf2","-salt","-in",blob,"-out",enc,"-pass","file:"+keyfile],check=True,capture_output=True)
        wrapped=subprocess.run(["openssl","pkeyutl","-encrypt","-pubin","-inkey",pem,"-pkeyopt","rsa_padding_mode:oaep","-pkeyopt","rsa_oaep_md:sha256"],input=password.encode(),check=True,capture_output=True).stdout
        cipher=base64.b64encode(open(enc,"rb").read()).decode()
        print("ENCRYPTED_KEY="+base64.b64encode(wrapped).decode())
        print("CIPHERTEXT_PARTS="+str((len(cipher)+3999)//4000))
        for i in range(0,len(cipher),4000):print("ENCRYPTED_PART_%03d="%int(i//4000)+cipher[i:i+4000])
        print("SNAPSHOT_READ_ONLY_PASS frames="+str(len(result["selected_frames"]))+" sha256="+hashlib.sha256(raw).hexdigest()[:16])
if __name__=="__main__":
    try:main()
    except Exception as e:print("SNAPSHOT_AUDIT_FAIL:"+type(e).__name__);sys.exit(1)
