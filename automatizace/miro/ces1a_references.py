"""Public, generic labels for the CES 1A methodological demo; no board data."""

HEURISTICS = [
    ("H01", "Odpovědný tým / útvar", "Kdo odpovídá za vznik události? Orgchart není automatická hranice."),
    ("H02", "Existující týmy", "Výchozí ownership; pozor na historické organizační řezy."),
    ("H03", "Předání mezi útvary", "Změna věcné odpovědnosti; předání samo o sobě nestačí."),
    ("H04", "Odlišní lidé a aktéři", "Jiné rozhodovací role a odborné kompetence."),
    ("H05", "Manuální × automatizovaný proces", "Rozdílná pravidla výjimek, nikoli jen technologie."),
    ("H06", "Externě zajišťovaný business", "Dodavatelské hranice; sourcing nemusí být doménová hranice."),
    ("H07", "Business KPI", "Samostatné výsledky a metriky odpovědnosti."),
    ("H08", "Business capability", "Inventář schopností; capability se automaticky nerovná doméně."),
    ("H09", "Doménová terminologie", "Odlišné významy stejných pojmů a vlastní pravidla."),
    ("H10", "Záměr uživatele", "Jaký business problém aktér potřebuje vyřešit?"),
    ("H11", "ES aktéři, systémy, pivotal events", "Pozorovatelné předěly z Event Stormingu; aplikace nejsou baseline."),
    ("H12", "User journey", "E2E cesta může procházet několika doménami."),
    ("H13", "Symetrie životního cyklu", "Vznik–změna–zánik; vlastní business lifecycle."),
    ("H14", "Nevratná skutečnost", "Právně či účetně významné rozhodnutí nebo závěr."),
    ("H15", "Odpovědní stakeholders", "Business owner a decision rights; neověřené role jsou OPEN."),
]

SOURCES = [
    ("S17", "Capability mapa L1/L2", "Odvozený pracovní inventář; ne potvrzené DDD domény"),
    ("S35", "Architektonický zápis 8. 9.", "Pracovní zápis; potvrzení L1 hranic neprokázáno"),
    ("S36", "Business perspektiva 8. 9.", "Pracovní návrh se společnou správou subjektů"),
    ("S47", "Architektonický overlay L0–L2", "Pracovní export; ne důkaz business ownership"),
    ("S48", "Architektonický zápis 22. 9.", "Draft rozšíření business rozsahu"),
    ("S49", "Architektonický zápis 6. 10.", "Novější pracovní diskuse a otevřené body"),
    ("S50", "Návrh řešení CES rev2", "Návrh modulů, ne DDD hranic"),
    ("S51", "Obecný rámec CES 13. 10.", "Draft capability/scope; ne schválená architektura"),
]
