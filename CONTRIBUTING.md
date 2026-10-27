# Contributing

Thanks for helping with Beam Bender. Small, focused pull requests are the
easiest to review. For a bigger change, please open an issue first so we can
agree on the idea.

## Run the game and the tests

```bash
pip install -r requirements.txt
python beam_bender.py     # play
python -m pytest          # unit tests
```

The game has no headless flag. CI (`.github/workflows/tests.yml`) runs the
unit tests and then starts the game in a virtual display (`xvfb-run`) with
audio off and renders a few frames. It runs on every push to `main` and on
every pull request.

## Add a level

Levels are the `LEVELS` list in `beam_bender.py`. Add a new dict to the end:

- `W`, `H`: grid width and height.
- `emit`: `((x, y), direction)` for the emitter, where direction is `R`, `L`,
  `U` or `D`.
- `fixed`: tiles that never move: `'#'` wall, `'T'` target, `'+'` splitter.
- `mirrors`: the cells the player can turn between `/` and `\`. They start as `/`.
- `targets`: the cells that must all be lit. List each one in `fixed` as `'T'` too.

`x` grows to the right and `y` grows towards the camera, so `(0, 0)` is the
back-left corner of the board.

`test_level_is_solvable` tries every mirror combination for every level, so
`python -m pytest` tells you if your new level can be solved.

## Add a feature

- The beam rules are in `trace()`. It is plain Python with no Panda3D, so it is
  easy to test. Please add a test to `test_beam_bender.py` for any new tile or rule.
- Drawing is done in `loadLevel()` and `refresh()`. Controls are set up in
  `BeamBender.__init__`.

## Add an asset

The game only uses shapes built in code and models that ship with Panda3D, so
there is no asset folder and nothing to download. Please keep it that way if
you can. If you do add an asset file, keep it small enough to commit.

## Licence and assets

- Assets must be CC0 or your own work. Please say where each asset comes from
  in your pull request.
- The code is MIT licensed (see `LICENSE`). By sending a contribution, you
  agree that it is released under the same MIT licence.
