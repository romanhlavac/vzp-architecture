#!/usr/bin/env python3
"""One-time READ ONLY CES demo snapshot via Miro REST v2.
Private content is RSA-3072 encrypted to an ephemeral external recipient before stdout.
Public repo stores public key and code only. No private text or IDs printed as plaintext.
Requires existing Actions Miro secrets. Never modifies Miro.
"""
import os,json,time,urllib.request,urllib.parse,urllib.error,subprocess,base64,tempfile,pathlib,hashlib,html,re
KEY="-----BEGIN PUBLIC KEY-----\nMIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAzrtvKjLG4EEY/JTiqWOV\nYkKW11PT+2jFOz1zd1jwFCy2yFMmIo9RNlBNQYI5wj7d8TUfVBhK67YU43noydse\nXIWkCmVnXFo6xTPovGwfuL1GKRcbrwg1WJtnauQQvXZSd5CxvsoqOz/fV5fdJPdi\nhFbpopuQSj1DJj8VKeLq6/aMPrxOji/DPj57tJbC1NvT/YctSH0w/ON7rLJjU/Su\nRqM0o+dm/3SNvaa5aPKGhfRk2fxM8llI7lQ+gHN9bmpfV4r3Uv+Aq14OQJLKuwl5\nwD5JE4FWTA9uC9L2SktohndwxQ3nYDRUJqHBjrp7cdurGW0Y0MVnN/DBIq1S1y3H\nbePDx/c1NE9hfx/EHitro7T442fTe5CMneksP16OXeZ3ax0VxAO29aXhCWVxPn1D\nERw2XERp7Rwuw02su572pHJsGkOlerdpaBR+L77EWgluxNzEHh+DOf8E8TqWK0Ru\nv7fhbkwgoCUJmq4KcLrFOyjLdohTKGgRS2+q3XJwADHNAgMBAAE=\n-----END PUBLIC KEY-----"
BOARD=os.environ["MIRO_DIAGNOSTIC_BOARD_ID"];TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
ROOT="https://api.miro.com/v2/boards/"+urllib.parse.quote(BOARD,safe="")+"/"
BP="3458764687741774534";DL="3458764687757375873"
BPDOC="3458764687806287544";DLDOC="3458764687803477373"
def req(path):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(ROOT+path,headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}),timeout=55) as f:
                return json.load(f)
        except urllib.error.HTTPError as ex:
            if ex.code in (429,500,502,503,504) and attempt<4:
                time.sleep(min(20,2**attempt));continue
            raise RuntimeError("MIRO_REST_HTTP_"+str(ex.code)+"_"+path.split("?")[0]) from None
        except (urllib.error.URLError,TimeoutError):
            if attempt<4:time.sleep(min(20,2**attempt));continue
            raise RuntimeError("MIRO_REST_TRANSPORT_"+path.split("?")[0]) from None
def listing(what,q=None):
    out=[];cur=None
    while True:
        p=dict(q or {});p["limit"]=50
        if cur:p["cursor"]=cur
        d=req(what+"?"+urllib.parse.urlencode(p))
        out.extend(d.get("data") or [])
        cur=d.get("cursor") or d.get("nextCursor")
        if not cur:return out
def keep(z):
    return {k:z.get(k) for k in ("id","type","parent","data","position","geometry","style","shape") if k in z}
def keepc(z):
    return {k:z.get(k) for k in ("id","startItem","endItem","shape","captions","style") if k in z}
def get():
    bp=listing("items",{"parent_item_id":BP})
    dl=listing("items",{"parent_item_id":DL})
    bp_st={str(z["id"]):z for z in bp if z.get("type")=="sticky_note"}
    dl_st={str(z["id"]):z for z in dl if z.get("type")=="sticky_note"}
    def plain(z):
        return " ".join(html.unescape(re.sub("<[^>]+>"," ",str((z.get("data") or {}).get("content") or ""))).split())
    bn={plain(z) for z in bp_st.values()};dn={plain(z) for z in dl_st.values()}
    if len(bp_st)!=147 or len(dl_st)!=147 or len(bn)!=147 or bn!=dn:raise RuntimeError("EVENT_SET_DRIFT")
    allc=listing("connectors")
    bpl=[z for z in allc if str((z.get("startItem") or {}).get("id")) in bp_st and str((z.get("endItem") or {}).get("id")) in bp_st]
    dll=[z for z in allc if str((z.get("startItem") or {}).get("id")) in dl_st and str((z.get("endItem") or {}).get("id")) in dl_st]
    if len(bpl)!=51 or len(dll)!=51:raise RuntimeError("RELATION_SET_DRIFT")
    docs={}
    for name,did,fid in (("bp",BPDOC,BP),("dl",DLDOC,DL)):
        d=req("docs/"+did+"?textContentType=markdown")
        c=str((d.get("data") or {}).get("content") or "")
        if len(c)<16000 or str((d.get("parent") or {}).get("id"))!=fid or not all(n in c for n in bn):
            raise RuntimeError("DOC_DRIFT_"+name)
        docs[name]={"id":did,"content":c}
    # Read only additional nearby items if needed later; export full parent-scoped live items.
    return {"meta":{"bp_frame":BP,"dl_frame":DL,"bp_count":len(bp_st),"dl_count":len(dl_st),
                    "bp_edges":len(bpl),"dl_edges":len(dll),"captured_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()},
            "bp_items":[keep(z) for z in bp],"dl_items":[keep(z) for z in dl],
            "bp_links":[keepc(z) for z in bpl],"dl_links":[keepc(z) for z in dll],"docs":docs}
def main():
    d=get()
    raw=json.dumps(d,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    with tempfile.TemporaryDirectory() as td:
        pub=pathlib.Path(td)/"public.pem";pub.write_text(KEY)
        # RSA 3072 PKCS1 v1.5; fresh random block padding; only encrypted bytes leave runner.
        blocks=[raw[k:k+360] for k in range(0,len(raw),360)]
        print("CES_SECURE_BEGIN",len(blocks),"plain_bytes",len(raw),flush=True)
        for i,part in enumerate(blocks):
            cp=subprocess.run(["openssl","pkeyutl","-encrypt","-pubin","-inkey",str(pub),
                               "-pkeyopt","rsa_padding_mode:pkcs1"],input=part,capture_output=True)
            if cp.returncode or len(cp.stdout)!=384:raise RuntimeError("ENCRYPTION_FAILED")
            print("CES_SECURE_BLOCK",i,base64.b64encode(cp.stdout).decode("ascii"),flush=True)
        print("CES_SECURE_END",len(blocks),flush=True)
    print("CES_PRIVATE_DATA_REDACTED; encrypted_payload_only; read_only",flush=True)
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("CES_SECURE_EXPORT_STOP",type(e).__name__,str(e),flush=True)
        raise SystemExit(1)
