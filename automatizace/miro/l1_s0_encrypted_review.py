#!/usr/bin/env python3
"""Read-only encrypted S0 event and L1 domain evidence. No client business text to CI logs."""
import os,sys,json,re,html,hashlib,pathlib,subprocess
from l1_v3_native_build import TITLE,BP_TITLE,RULES,listing,txt,oid,parent,edge
ROOT=pathlib.Path(__file__).parent
def take():
  frames=listing("items",{"type":"frame"})
  lm=[z for z in frames if (z.get("data") or {}).get("title")==TITLE]
  bm=[z for z in frames if (z.get("data") or {}).get("title")==BP_TITLE]
  if len(lm)!=1 or len(bm)!=1:raise RuntimeError("FRAME_DRIFT")
  l1=listing("items",{"parent_item_id":oid(lm[0])})
  bp=listing("items",{"parent_item_id":oid(bm[0])})
  s0=set(RULES["groups"]["S0"])
  originals=[z for z in bp if z.get("type")=="sticky_note" and hashlib.sha256(txt(z).encode()).hexdigest() in s0]
  cards=[z for z in l1 if z.get("type")=="sticky_note" and hashlib.sha256(txt(z).encode()).hexdigest() in s0]
  if len(s0)!=19 or len(originals)!=19 or len(cards)!=19:raise RuntimeError("S0_19_CARDS_DRIFT")
  ds=[]
  for source in originals:
    marker="?moveToWidget="+oid(source)
    matches=[z for z in l1 if z.get("type")=="text" and marker in str((z.get("data") or {}).get("content") or "")]
    ds.append({"source_id":oid(source),"source_event":txt(source),"desc":txt(matches[0]) if len(matches)==1 else None,"description_match_count":len(matches)})
  domains=[{"text":txt(z),"type":z.get("type")} for z in l1 if z.get("type")=="shape" and
       ("Správa a evidence subjektů" in txt(z) or re.search(r"\bS0\b",txt(z)))]
  if not domains:raise RuntimeError("S0_DOMAIN_DESCRIPTION_MISSING")
  record={"l1_title":TITLE,"count_s0":len(cards),"events":ds,"domains":domains,
          "frame_counts":{typ:sum(z.get("type")==typ for z in l1) for typ in ("sticky_note","text","shape","doc_format")}}
  dst=pathlib.Path("s0-evidence")
  dst.mkdir(exist_ok=True)
  plain=dst/"s0.json";cipher=dst/"s0.p7m"
  plain.write_text(json.dumps(record,ensure_ascii=False),encoding="utf-8")
  try:
    enc=subprocess.run(["openssl","cms","-encrypt","-binary","-aes-256-cbc",
       "-in",str(plain),"-outform","DER","-out",str(cipher),
       str(ROOT/"l1_s0_20261020_ephemeral.crt")],capture_output=True,timeout=15)
    if enc.returncode:raise RuntimeError("ENCRYPTION_FAIL")
  finally:plain.unlink(missing_ok=True)
  print("S0_ENCRYPTED_LIVE_READ_PASS","S0=19","linkedDescriptions=19",
        "encryptedBytes="+str(cipher.stat().st_size),flush=True)
if __name__=="__main__":
  try:take()
  except Exception as e:print("S0_ENCRYPTED_LIVE_READ_STOP",type(e).__name__,str(e));sys.exit(1)
