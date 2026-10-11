# Rūretto 3D (Crayon Engine)

A full 3D port of [Rūretto](https://github.com/2dprototype/Ruretto) for the Crayon Engine.
Same colours (`theme.td`), same wheel order (`wheel.td`), same bet ids and payouts (`rules.td`),
same chip values, history panel and save-game behaviour - now with a physical ball.

## Run
Open this folder with Crayon (entry point: `main.lua`). All assets are already generated.
To regenerate / tweak them:

    pip install pillow numpy
    python tools/generate_assets.py        # models (.obj), textures (.png), sounds (.wav)

## Controls
| Input | Action |
|---|---|
| Mouse click on felt | place a chip on that bet |
| Click chips / buttons (bottom) | choose chip value, CLEAR, DOUBLE, ALL, SPIN |
| SPACE | spin | 
| C / D / A | clear / double / all-in chip |
| LEFT / RIGHT | change chip value |
| V | toggle table / wheel camera |
| H | history panel |
| F1 / F2 | physics debug view / retro CRT look |

## Touch / Android
* Tap the felt to place a chip (the bet is placed when the finger lifts, so you can slide to aim; the cell highlights while you hold).
* Bottom bar buttons are larger on touch devices; **VIEW** (top right) switches table / wheel camera, the clock icon opens history.
* The Android Back button (`escape`) closes history, returns to the table camera, then quits.
* Mouse events synthesised from touches are ignored, so a tap never places two chips.

## How it works
* `tools/generate_assets.py` builds everything procedurally: bowl, ball track, rotor (37 pockets + frets + hub),
  ball, chips, marker, table, betting felt, carpet; textures use the original colours and the original font.
* Physics3D: static mesh bowl, kinematic rotating floor + 37 kinematic frets, dynamic CCD ball with damping.
  The winning pocket is whichever one the ball actually settles in (position relative to the rotor angle).
  Safety nets: relaunch if the ball leaves the bowl, forced settle after 28 s.
* Rules are unchanged except two fixes of bugs in the original: EVEN no longer pays on 0,
  and DOUBLE no longer charges the bet twice.

## If something looks off
Two switches at the top of `main.lua`:
* `ROT_DEGREES` - set `true` if your build's `drawModel` rotations are degrees.
* `ROT_SIGN` - set `-1` if the rotor spins opposite to the physics frets (check with F1).
If textures appear upside-down, set `FLIP_V = True` in the generator and re-run it.

MIT licensed (see LICENSE), derived from the original Rūretto.
