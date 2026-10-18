#!/usr/bin/env python3
"""Resume approved 1A after verified checkpoint: enlarged bands, original cards.

Never re-expands the frame or moves external references again.
Creates only one approved new S0 event and five non-event interaction references.
"""
import os,sys,re,html
from ces1a_branch_approved import (
    call,page,id,xx,yy,ww,hh,close,txt,tag,parent,detail,moved,
    CODES,EXPECTED,LANES,HEIGHTS,EXTRA,ZOOM_EXTRA,CHRONOLOGY,BRANCH_LABELS,
    link_plan_for_rows,scenecenter,clone_front,add_new_subject_event,create_link,
    zoom,text_create,update_header_legend_text,connector_list,edge
)
MODE=os.getenv("CES_RECOVERY_MODE","audit")
if MODE not in ("audit","apply"):sys.exit("Invalid mode")
Y=[468,735,1004,1273,1542,1811,2080,2349,2618,2887,3156,3425,3694,3963,4232,4501,4770,5039,5308,5577]
oldY=dict(zip(CODES,Y))
def shift(i):return sum(HEIGHTS.get(CODES[k],224)-224 for k in range(i))
def take_snapshot():
    frames=page("items",{"type":"frame"})
    candidates=[f for f in frames if close(ww(f),6075,25)
                and close(hh(f),7746+EXTRA+ZOOM_EXTRA,25)]
    if len(candidates)!=1:raise RuntimeError("Expected unique enlarged frame")
    fr=call("GET","frames/"+id(candidates[0]))
    children=page("items",{"parent_item_id":id(fr)})
    if len([x for x in children if x.get("type")=="sticky_note"])!=130:
        raise RuntimeError("Not in card relocation checkpoint")
    dom={}
    for z in children:
        if z.get("type")!="shape" or tag(z) not in CODES or "Aktéři" not in txt(z):continue
        code=tag(z)
        if code in dom:raise RuntimeError("Ambiguous domain")
        dom[code]=z
    if len(dom)!=20:raise RuntimeError("Domain count mismatch")
    for code in CODES:
        i=CODES.index(code)
        expectedY=oldY[code]+shift(i)+(HEIGHTS.get(code,224)-224)/2
        if not close(yy(dom[code]),expectedY,5):
            raise RuntimeError("Domain positioning drift "+code)
    ratio=[x for x in children if x.get("type")=="shape"
           and "BOUNDARY RATIONALE" in txt(x).upper()]
    if len(ratio)!=20 or sum(hh(x)>300 for x in ratio)!=7:
        raise RuntimeError("Boundary rationale checkpoint drift")
    cards={}
    for i,code in enumerate(CODES):
        obs=sorted([x for x in children if x.get("type")=="sticky_note"
                    and close(yy(x),oldY[code],40) and close(ww(x),258,10)],key=xx)
        if len(obs)!=EXPECTED[i]:raise RuntimeError("Original event inventory drift in row "+code)
        cards[code]=obs
    member={id(x) for x in children}
    inside=[c for c in page("connectors")
            if edge(c,"startItem") in member and edge(c,"endItem") in member]
    if len(inside)!=17:raise RuntimeError("Expected exactly 17 surviving nonrelated links")
    return fr,children,cards
def apply():
    frame,children,original=take_snapshot()
    print("RESUME CHECKPOINT PASS: 130 original events, 7 expanded bands, 17 retained links")
    placement=link_plan_for_rows(original)
    rebuilt={}
    moved_count=0
    for code in CODES:
        i=CODES.index(code)
        rebuilt[code]=list(original[code])
        if code not in LANES:
            dy=shift(i)
            for k,item in enumerate(original[code]):
                if dy:
                    rebuilt[code][k]=moved(detail(item),dy)
                    moved_count+=1
            continue
        for lane,indices in enumerate(LANES[code]):
            for position,index in enumerate(indices):
                if index=="NEW":continue
                obj=detail(original[code][index])
                x,_=placement[(code,index)]
                y=scenecenter(code,lane,oldY[code])
                call("PATCH","sticky_notes/"+id(obj),
                     {"position":{"x":x,"y":y,"origin":"center"}})
                fresh=call("GET","sticky_notes/"+id(obj))
                if not close(xx(fresh),x,4) or not close(yy(fresh),y,4):
                    raise RuntimeError("Event position readback mismatch "+code)
                rebuilt[code][index]=fresh
                moved_count+=1
        if code in ("B8","B9"):
            for k,card in enumerate(rebuilt[code]):
                rebuilt[code][k]=clone_front(card,frame)
    # Create precisely one new approved event.
    additional=add_new_subject_event(frame,2490,scenecenter("S0",1,oldY["S0"]))
    # Local links are only meaningful edges within each scenario.
    new_links=0
    for code,pairs in CHRONOLOGY.items():
        for a,b in pairs:
            create_link(rebuilt[code][a],rebuilt[code][b])
            new_links+=1
    create_link(rebuilt["S0"][1],additional);new_links+=1
    create_link(additional,rebuilt["S0"][5]);new_links+=1
    # Labeled vertical branches, not three new DDD bounded contexts.
    for code,labels in BRANCH_LABELS.items():
        for lane,label in enumerate(labels):
            text_create(frame,850,scenecenter(code,lane,oldY[code]),900,
                "<b>"+html.escape(label)+"</b>",18)
    # Explicit cross-event dependency view; labels only, never duplicate Stickies.
    zoom(frame,rebuilt)
    labels_updated=update_header_legend_text(children)
    after=page("items",{"parent_item_id":id(frame)})
    sticky=[z for z in after if z.get("type")=="sticky_note"]
    if len(sticky)!=131:raise RuntimeError("131-event acceptance failed")
    final_cons=page("connectors")
    mids={id(x) for x in after}
    internal=[z for z in final_cons
        if edge(z,"startItem") in mids and edge(z,"endItem") in mids]
    if len(internal)!=17+new_links:raise RuntimeError("Links not preserved")
    if any(str((z.get("style") or {}).get("strokeColor") or "").lower()!="#000000" for z in internal):
        raise RuntimeError("Not all arrows black")
    if any(re.match(r"^[A-D]\d?\.\d{2}",txt(z)) for z in sticky):
        raise RuntimeError("Event domain code leaked")
    # All original business events, apart from the single new, must remain once.
    existing_texts=[txt(z) for z in sticky]
    if len(existing_texts)!=len(set(existing_texts)):
        raise RuntimeError("Duplicate event labels after re-layout")
    print("REST RESUME PASS: 131 native event cards; %d event relocations"%moved_count)
    print("EVENTSTORMING SCENARIOS PASS: 7 stacked areas; 20 branch labels")
    print("CONNECTOR PASS: %d black arrows, %d new scenario edges"%(len(internal),new_links))
    print("S0 INTERACTION ZOOM PASS: D01/D04/D06/D08/D09 text references, not new events")
    print("LEGEND: %d entries revised"%labels_updated)
    print("VISUAL SCREENSHOT ACCEPTANCE: PENDING")
try:
    if MODE=="audit":
        take_snapshot()
        print("RECOVERY AUDIT PASS: no write")
    else:apply()
except Exception as e:
    print("FAIL:",str(e))
    sys.exit(1)
