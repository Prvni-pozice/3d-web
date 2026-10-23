# Polep GTX #89

Generuje `../ktm-gtx-89.glb`: model `ktm-gtx.glb` s polepem vozu #89 (červeno-černý, JR, startovní čísla).

## Postup

Blender 4.2 (portable v `~/opt/blender-4.2.3-linux-x64/`, knihovny přes
`LD_LIBRARY_PATH=~/opt/blibs/root/usr/lib/x86_64-linux-gnu`):

1. `blender -b -P prep.py -- 4096` — spojí skořepinu (lak + karbon) do jednoho meshe,
   udělá novou UV mapu a vypeče do `work/` světovou pozici a normálu každého texelu.
2. `python3 livery.py` — z pozic/normál spočítá texturu polepu (`work/livery.jpg`
   + `work/livery_mr.png` s drsností). Polep je kreslený jako 2D vrstvy v rovinách
   shora / bok / předek / záď (souřadnice v metrech), tady se ladí vzhled.
   Sponzoři jsou v `logos.py` jako typografické náhrady (podoba podle fotek, ne originální
   vektorová loga — ta by šla vyměnit, kdyby byly k dispozici soubory).
3. `blender -b -P build.py -- render <prefix> [pohledy]` — náhledy (pohledy v `common.py`),
   `blender -b -P build.py -- export ../ktm-gtx-89.glb` — export.

Pro ladění polepu stačí opakovat krok 2 a 3, `prep.py` jen při změně geometrie/UV.
`gridviews.py` domaluje do ortho renderů mřížku v metrech.

## Licence

- Model: Ddiaz Design, Sketchfab, CC-BY-NC-SA 4.0 → upravený model je pod stejnou
  licencí, jen nekomerčně.
- Fonty: Russo One (čísla), Barlow / Barlow Condensed, Montserrat — vše SIL OFL.
- Loga sponzorů a GT2 Europe jsou ochranné známky jejich vlastníků; jen pro nekomerční prototyp.
