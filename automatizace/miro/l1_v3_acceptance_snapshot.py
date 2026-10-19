#!/usr/bin/env python3
"""Independent read-only encrypted v3 acceptance source for complete catalog deliverable."""
import os,sys,json,pathlib,subprocess,collections
from landscape_snapshot import listing
from l1_v3_native_build import TITLE,BP_TITLE,oid,parent,edge,txt
from landscape_build import RULES
ROOT=pathlib.Path(__file__).parent
def main():
    items=listing("items");conn=listing("connectors")
    frames=[z for z in items if z.get("type")=="frame"]
    targets=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
    bps=[z for z in frames if (z.get("data") or {}).get("title")==BP_TITLE]
    if len(targets)!=1 or len(bps)!=1:raise RuntimeError("FRAME_MISSING_OR_AMBIGUOUS")
    target=targets[0];bp=bps[0]
    children=[z for z in items if parent(z)==oid(target)]
    bpchildren=[z for z in items if parent(z)==oid(bp)]
    ids={oid(z) for z in children}
    link=[z for z in conn if edge(z,"startItem") in ids and edge(z,"endItem") in ids]
    totals=collections.Counter(z["type"] for z in children)
    if totals["sticky_note"]!=147 or totals["shape"]!=142 or totals["text"]!=203 or len(link)!=51:
        raise RuntimeError("TARGET_COUNTS_FAIL_"+str(dict(totals))+"_links_"+str(len(link)))
    if len([z for z in bpchildren if z.get("type")=="sticky_note"])!=147:
        raise RuntimeError("BP_SOURCE_DRIFT")
    paths=pathlib.Path("encrypted-v14-l1");paths.mkdir(exist_ok=True)
    plain=paths/"landscape-v3.json";cipher=paths/"landscape-v3.p7m"
    record={"source_bp":bp,"target_frame":target,"items":children,"connectors":link,"source_events":
            [z for z in bpchildren if z.get("type")=="sticky_note"]}
    plain.write_text(json.dumps(record,ensure_ascii=False),encoding="utf-8")
    p=subprocess.run(["openssl","cms","-encrypt","-binary","-aes-256-cbc",
       "-in",str(plain),"-outform","DER","-out",str(cipher),
       str(ROOT/"l1_v3_ephemeral_receiver.crt")],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    plain.unlink()
    if p.returncode:raise RuntimeError("ENCRYPTION_ERROR")
    print("INDEPENDENT_ENCRYPTED_ACCEPTANCE_PASS",dict(totals),"relations",len(link),
          "encrypted_bytes",cipher.stat().st_size)
if __name__=="__main__":
    try:main()
    except Exception as e:print("INDEPENDENT_STOP",type(e).__name__,str(e));sys.exit(1)
