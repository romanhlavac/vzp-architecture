# CES DEMO 1B — reorganizace 2026-10-23

Status: **IMPLEMENTED / G4 OPEN**. Výhradně metodické DEMO, nikoli target návrh VZP ani business sign-off.

## Provedené změny

- Fresh bootstrap aktuálních projektových instrukcí, manifestu, jádra, Source Indexu, metodiky 1B/1C, quality gates a Miro skillu z kanonického Google Drive.
- Načten celý realizační ZIP `CES_DEMO_1B_REALIZACE_BALICEK_20261023.zip`; použit jako PROJECT_SUPPORT/NON_EVIDENCE.
- Bezpečný REST preflight; pilotní přesun Inventory s kontrolou identity, polohy, 11 původních dětí, obsahu, stylů a incidentních vazeb.
- Zachováno původních 49 framů a původní widget IDs; výsledkem je 65 framů. Žádný původní widget nebyl mazán ani nahrazen rasterem.
- Hlavní řada 1B zleva doprava podle zadání, pod 1A. Finální horní hrana hlavní řady y=30000 odděluje trasu od historické ilustrace.
- Pět nativních karet zdůvodnění scénářů; evidence clustering; důvody S0.1/S0.2, alternativy a OPEN; nativní navigace.
- Inventory rozšířen na pět scénářů při zachování existujících IDs.
- 1C je napravo od závěru 1B; kroky 2–5 jsou v samostatných pásmech níže, pouze PLANNED.
- Historické a referenční objekty zachovány a odděleny od MAIN. Neorámovaná historická DDD ilustrace zůstala na původním místě a byla vizuálně označena referenčním framem; její původní objekty nebyly přesouvány.
- Opraven překryv výsledných událostí a překrytí patičkou v SC-05; výjimková vazba vede vně karet.
- Nativně odstraněny zastaralé řídicí body referenční a metodické spojnice; endpoint IDs zachovány. Upraveno lokální trasování.
- Zlepšena čitelnost syntetických karet, inventáře a metodického úvodu.
- BP v14 a L1 DL v3 nebyly měněny; kontroly chráněných framů, obsahu a vazeb při jednotlivých zápisových etapách prošly.
- Miro AI nebylo použito. Tokeny nebyly vloženy do kódu ani logů.
- Workflow ponecháno v `STORY_MODE: verify`; read-back konfigurace odpovídá očekávanému obsahu.

## G1–G4

| Gate | Výsledek | Evidence a omezení |
|---|---|---|
| G1 — sémantika | PASS v rozsahu metodického DEMO | Kandidáti/OPEN odděleni od validovaných hranic; scénářové heuristiky a důvody L2 zobrazeny. Nejde o business validaci VZP. |
| G2 — native struktura | PASS | Všech 16 nových framů ověřeno v REST, nativní editovatelné karty; původní IDs zachovány; 703 spojnic. |
| G3 — geometrie | PASS — strukturální proxy | Poslední read-only běh: 26 dotčených framů, 0 překryvů bounding boxes. Tato kontrola není vizuální acceptance. |
| G4 — živá vizuální acceptance | OPEN / částečně provedeno | Proběhla reálná kontrola Cloud Browserem a opravy. Browser se stal nedostupným před úplným závěrečným průchodem. |

Vizuálně ověřeno: SC-01 včetně pracovního zoomu; SC-02; SC-03 a SC-04 po oddělení historické kresby; SC-05 po opravě patičky, událostí a výjimkové vazby; čtecí navigace a její živý odkaz na SC-03; karta výběru SC-01; Evidence clustering před finálním zvětšením písma; Boundary rationale po zvětšení písma. U metodické vazby byly v živém Miro odstraněny vzdálené body a lokálně upraven koridor.

### OPEN pro uzavření G4

1. V živém Miro zkontrolovat metodický úvod po poslední změně písma (20 původních položek, 6 spojnic; REST read-back PASS).
2. Dokončit finální vizuální průchod E2E syntézou, výslednou referenční spojnicí a přehledem celé trasy/pásem.
3. Ověřit finální vykreslení zvětšeného Evidence clustering a všechny varianty karet „Proč tento scénář“.

Nejsou tvrzeny nepozorované vizuální výsledky. Omezení je nedostupnost Cloud Browseru v závěru, nikoli neúspěch posledního REST běhu.

Business OPEN zůstávají záměrně v DEMO: autorita a předání externích změn, alternativy hranic, reviewer/owner a validace v 1C. Kroky PLANNED nejsou prohlašovány za realizované.

## Kanonické soubory

- [VZP_MIRO_MODELING_SKILL.md](https://drive.google.com/file/d/1WSsWD59HweBS5ncb9ya72g9BrdaS08CC/view), v2.2.3, 46409 bytes, SHA-256 `d68a9bd9a3a01f04ab1fb646a6f8dadf12b9b31f7644ba2c903a2ae2460f4a5f`.
- [VZP_SKILLS_MANIFEST.md](https://drive.google.com/file/d/1XZWe0Yh9aikDM_Bu0R4jw57sRwe3Pj6M/view), v1.0.4, 10359 bytes, SHA-256 `45156d016dfcd9bcbc4b9d8d4e8d39730b2b55b2c48636d31cdd7781ab9045b4`.
- Poslední čerstvý read-back obou Drive souborů je shodný s ověřenými bajty a manifestem. Drive IDs zachována.
- Source Index zůstává v5.0; nebyl předstírán refresh business evidence.

## Kontrolní běhy

- [REST preflight](https://github.com/romanhlavac/vzp-architecture/actions/runs/39953094044)
- [Pilot](https://github.com/romanhlavac/vzp-architecture/actions/runs/39953269201)
- [Oddělení historické ilustrace](https://github.com/romanhlavac/vzp-architecture/actions/runs/39958961292)
- [SC-05 patička a trasování](https://github.com/romanhlavac/vzp-architecture/actions/runs/39960217844)
- [Poslední úprava písma metodiky](https://github.com/romanhlavac/vzp-architecture/actions/runs/39961425554)
- [Finální read-only verification — SUCCESS](https://github.com/romanhlavac/vzp-architecture/actions/runs/39961507731): 16 nových framů PASS; 703 spojnic PASS; 26 framů / 0 překryvů; G1/G2 PASS, G4 OPEN.

Dřívější přerušené běhy (REST 500, následná oprava formátu font size a souběžná změna routingu zachycená kontrolou EDGE_DRIFT) nejsou vydávány za úspěšnou acceptance; dokončení bylo ověřeno novými samostatnými běhy.

## Výsledné framy

| Frame | Odkaz |
|---|---|
| Vstupní navigace | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487258) |
| Scenario Inventory | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687949068244) |
| Metodika A–E | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688162404596) |
| SC-01 | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687939229431) |
| SC-02 | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687939229785) |
| SC-05 | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688202201527) |
| SC-03 | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687939406397) |
| SC-04 | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687949762980) |
| E2E syntéza | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687942876552) |
| Evidence clustering | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688217500338) |
| Kandidátní L2 mapa | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764687938964779) |
| Boundary rationale / 1C | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688217622063) |
| SC-01 — proč | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487020) |
| SC-02 — proč | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487153) |
| SC-05 — proč | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487185) |
| SC-03 — proč | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487221) |
| SC-04 — proč | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487238) |
| 1C PLANNED | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487305) |
| 2 PLANNED | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487321) |
| 3 PLANNED | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487335) |
| 4 PLANNED | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487411) |
| 5 PLANNED | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688218487433) |
| Historická Process Modelling reference | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688162124320) |
| Historická DDD ilustrace | [Otevřít](https://miro.com/app/board/uXjVHiylz-0=/?moveToWidget=3458764688220126880) |
