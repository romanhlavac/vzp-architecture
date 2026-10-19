#!/usr/bin/env python3
"""Read-only V14/L1v2 snapshot encrypted for analyst-side semantic review."""
import os,sys,json,html,re,hashlib,urllib.parse,urllib.request,urllib.error,time,pathlib,subprocess,collections
from landscape_snapshot import listing
from landscape_build import RULES, tx
ROOT=pathlib.Path(__file__).parent
TITLE_BP="CES-1A · BP ES v14 · Enterprise business events · pracovní návrh"
TITLE_L1="CES-1A · L1 DOMAIN LANDSCAPE · v2 (BP ES v12 mapping)"
def eid(z):return str(z.get("id",""))
def parent(z):return str((z.get("parent") or {}).get("id") or "")
def relation(z,k):return str((z.get(k) or {}).get("id") or "")
def main():
    allitems=listing("items");allcons=listing("connectors")
    frames=[z for z in allitems if z.get("type")=="frame"]
    source=[z for z in frames if (z.get("data") or {}).get("title")==TITLE_BP]
    prev=[z for z in frames if (z.get("data") or {}).get("title")==TITLE_L1]
    template=[z for z in frames if hashlib.sha256(eid(z).encode()).hexdigest()==RULES["template_frame_id_hash"]]
    if len(source)!=1 or len(prev)!=1 or len(template)!=1:raise RuntimeError("Frame mismatch")
    bp=[z for z in allitems if parent(z)==eid(source[0])]
    pv=[z for z in allitems if parent(z)==eid(prev[0])]
    tmpl=[z for z in allitems if parent(z)==eid(template[0])]
    notes=[z for z in bp if z.get("type")=="sticky_note"]
    ids={eid(z) for z in notes}
    cons=[z for z in allcons if relation(z,"startItem") in ids and relation(z,"endItem") in ids]
    if len(notes)!=147 or len(cons)!=51:raise RuntimeError("Current source inventory drift")
    old_h={h for vs in RULES["groups"].values() for h in vs}
    original=sum(hashlib.sha256(tx(z).encode()).hexdigest() in old_h for z in notes)
    if original!=110:raise RuntimeError("Missing original 110")
    data={"source_frame":source[0],"v2_frame":prev[0],"template":template[0],
          "bp_notes":notes,"bp_connectors":cons,
          "l1v2_items":pv,"template_items":tmpl,
          "counts":{"bp":len(notes),"connectors":len(cons),"v2":len(pv),"template":len(tmpl)}}
    d=pathlib.Path("encrypted-v14-l1");d.mkdir(exist_ok=True)
    plain=d/"inventory.json";cipher=d/"inventory.p7m"
    plain.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    c=subprocess.run(["openssl","cms","-encrypt","-binary","-aes-256-cbc","-in",str(plain),
       "-outform","DER","-out",str(cipher),str(ROOT/"l1_v3_ephemeral_receiver.crt")],
        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    plain.unlink()
    if c.returncode!=0:raise RuntimeError("Evidence encryption failed")
    print("READ_ONLY_ENCRYPTED_SNAPSHOT_PASS","bp_events",len(notes),"relationships",len(cons),
          "original_v12_events",original,"v2_items",len(pv),"template_items",len(tmpl),
          "encrypted_bytes",cipher.stat().st_size)
if __name__=="__main__":
    try:main()
    except Exception as e:print("SNAPSHOT_STOP",type(e).__name__,str(e));sys.exit(1)
