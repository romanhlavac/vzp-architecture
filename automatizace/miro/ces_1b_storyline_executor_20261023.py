#!/usr/bin/env python3
"""Move explicitly listed CES DEMO frames with Miro REST v2; dry-run default."""
import os,json,urllib.request,urllib.parse
BASE="https://api.miro.com/v2/boards/"+urllib.parse.quote(os.environ["MIRO_DIAGNOSTIC_BOARD_ID"],safe="")+"/"
TOKEN=os.environ["MIRO_DIAGNOSTIC_TOKEN"]
def api(verb,path,body=None):
    data=json.dumps(body).encode() if body else None
    hdr={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"}
    req=urllib.request.Request(BASE+path,method=verb,data=data,headers=hdr)
    with urllib.request.urlopen(req,timeout=50) as r: return json.load(r)
def main():
    fid="3458764687949068244"
    frame=api("GET","frames/"+fid)
    assert "Identifikace procesních scénářů" in frame["data"]["title"]
    print("READ_ONLY_PREFLIGHT",fid,frame["position"])
    mode=os.environ.get("STORY_MODE","audit")
    if mode=="pilot":
        desired={"data":{"title":"CES DEMO · 1B.01 · Výběr scénářů · MAIN"},"position":{"x":224700,"y":28800,"origin":"center"}}
        api("PATCH","frames/"+fid,desired)
        verified=api("GET","frames/"+fid)
        assert verified["data"]["title"]==desired["data"]["title"]
        assert abs(verified["position"]["x"]-224700)<2
        assert abs(verified["position"]["y"]-28800)<2
        print("STORY_PILOT_PASS",fid)
if __name__=="__main__":main()
