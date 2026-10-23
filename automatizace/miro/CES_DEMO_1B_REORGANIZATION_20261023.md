# CES DEMO 1B — reorganizace 2026-10-23

Status: **IMPLEMENTED / G1–G4 PASS — metodické DEMO**. Výhradně metodické DEMO, nikoli target návrh VZP ani business sign-off.

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
| G4 — živá vizuální acceptance | PASS | Zbývající skutečný native render ověřen Cloud Browserem 2026-10-23; konkrétní vady opraveny a znovu vizuálně zkontrolovány. |

Vizuálně ověřeno: SC-01 včetně pracovního zoomu; SC-02; SC-03 a SC-04 po oddělení historické kresby; SC-05 po opravě patičky, událostí a výjimkové vazby; čtecí navigace a její živý odkaz na SC-03; karta výběru SC-01; Evidence clustering před finálním zvětšením písma; Boundary rationale po zvětšení písma. U metodické vazby byly v živém Miro odstraněny vzdálené body a lokálně upraven koridor.

### Uzavření G4 — 2026-10-23

Na pokyn uživatele nebyla zahájena nová reorganizace ani další metodická implementace. Návazná práce zahrnovala pouze aktuální kontrolu, opravy pozorovaných vizuálních vad a tento report.

**Dokončený vizuální průchod:** Metodika A–E po finální opravě textů a koridoru spojnice; Inventory po opravě přesahů; E2E syntéza v celku i 50% detailu; Evidence clustering a Boundary rationale po zvětšení písma; kandidátní L2 mapa; všech pět karet „Proč tento scénář“ včetně opraveného H1/H3 u SC-01; referenční Process Modelling; historická DDD ilustrace; přehled 1A/1B a pásem 2–5; samostatně PLANNED 1C, 2, 3, 4 a 5. Navigační karta byla přečtena a její živý odkaz na SC-05 skutečně otevřen; výsledný SC-05 render znovu ověřen bez překryvu událostí/patičky.

**Opravy zjištěné při G4:**
- Metodika A–E: šest původních textů mělo po změně písma příliš široké boxy; opraveny šířky a pozice, spodní poznámka oddělena od Read Model, vysvětlující text vyveden z koridoru Policy → Command. Zachovány text, styl, typ, parent a IDs: `3458764688162404600`, `3458764688162404606`, `3458764688162404609`, `3458764688162404610`, `3458764688162404618`, `3458764688162543828`.
- Inventory: opraven přesah pěti textů; obsah, barvy a odkazy zachovány. IDs: `3458764687949762944`, `3458764687949762956`, `3458764687949762969`, `3458764687949762978`, `3458764688162542993`.
- Reference Process Modelling: lokálně upraven oblouk spojnice `3458764688199613665` s popiskem „Business causality. Implementation unspecified.“; původní Hotspot a Query Model / Information posunuty mimo její koridor. Stejné nativní objekty, zachován směr Command / Action → Domain Event, popisek i typ křivky. Není tvrzen nulový počet všech křížení; odstraněny průniky do karet a kolize popisku.
- Historická DDD ilustrace: rám `3458764688220126880` překrýval původní neparentované objekty bílou plochou. Nativní akcí **Send to back** byl poslán do pozadí. Původní ilustrace je znovu viditelná; její objekty nebyly přesouvány ani přepisovány.

**Kontrola změn:** nevytvořen ani smazán žádný frame; 65 framů a 703 spojnic zachováno. Cílené REST opravy mají kontrolu obsahu/identity/protected read-back; UI opravy byly ověřeny skutečným renderem. BP v14 a L1 DL v3 nebyly editovány. Automatizace zůstává v `STORY_MODE: verify`, přesný read-back konfigurace PASS.

**Výsledné vizuální vady OPEN: žádné zjištěné v kontrolovaném rozsahu.** Šedý nápis „Developer team“ je vodoznak prostředí Miro, nikoli modelový widget. Předchozí omezení dostupnosti browseru bylo při tomto průchodu překonáno; G4 PASS je založen na dokončených pozorováních, nikoli na CI statusu.

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
- [Předchozí read-only verification — SUCCESS](https://github.com/romanhlavac/vzp-architecture/actions/runs/39961507731): 16 nových framů PASS; 703 spojnic PASS; 26 framů / 0 překryvů; G1/G2 PASS, G4 OPEN.

- [G4 oprava metodických textů — SUCCESS](https://github.com/romanhlavac/vzp-architecture/actions/runs/39966486000): šest textů, obsah/IDs/vazby/protected read-back PASS.
- [G4 uvolnění koridoru metodické spojnice — SUCCESS](https://github.com/romanhlavac/vzp-architecture/actions/runs/39967248374).
- [G4 oprava textů Inventory — SUCCESS](https://github.com/romanhlavac/vzp-architecture/actions/runs/39967679292): pět textů, obsah/IDs/vazby/protected read-back PASS.
- [Finální read-only verification — SUCCESS, attempt 2](https://github.com/romanhlavac/vzp-architecture/actions/runs/39968068652): job `120465307117`, dokončeno 2026-10-23 14:21 UTC po poslední UI opravě vrstvení; 16 očekávaných nových framů PASS, 65 framů, 703 spojnic, 26 dotčených framů / 0 bbox překryvů. Automatický log záměrně stále uvádí `G4_OPEN`, protože REST nemůže potvrdit vizuální gate; jeho uzavření dokládá výše popsaný samostatný živý průchod.
- První cílený G4 běh `39965903235` skončil na `TEXT_Y_SCOPE` po částečné opravě pěti textů. Read-only audit identifikoval šestý text na y=2161; následný idempotentní běh opravu dokončil. Tento přerušený běh není vydáván za PASS.

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
