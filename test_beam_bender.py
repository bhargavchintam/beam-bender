"""Unit tests for the pure beam-tracing logic in beam_bender.py."""
from itertools import product

import pytest

from beam_bender import LEVELS, ccw, trace


def test_slash_mirror_reflects_beam():
    # Beam heads right, hits '/' at (1,1), should turn to head up (U) and hit
    # the target directly above the mirror.
    tiles = {(1, 1): "/", (1, 0): "T"}
    lit, segs = trace(3, 3, tiles, ((0, 1), (1, 0)))
    assert lit == {(1, 0)}
    assert (1, 1, 1, 0) in segs


def test_backslash_mirror_reflects_beam():
    # Beam heads right, hits '\' at (1,1), should turn to head down (D) and
    # hit the target directly below the mirror.
    tiles = {(1, 1): "\\", (1, 2): "T"}
    lit, _ = trace(3, 3, tiles, ((0, 1), (1, 0)))
    assert lit == {(1, 2)}


def test_wall_stops_the_beam():
    tiles = {(1, 0): "#"}
    lit, segs = trace(3, 1, tiles, ((0, 0), (1, 0)))
    assert lit == set()
    assert segs == [(0, 0, 1, 0)]


def test_target_lights_and_stops_the_beam():
    tiles = {(1, 0): "T"}
    lit, segs = trace(2, 1, tiles, ((0, 0), (1, 0)))
    assert lit == {(1, 0)}
    assert segs == [(0, 0, 1, 0)]


def test_splitter_sends_the_beam_both_ways():
    # '+' forwards the beam straight (R) and turned 90deg ccw (U); each branch
    # should independently reach and light its own target.
    tiles = {(1, 1): "+", (2, 1): "T", (1, 0): "T"}
    lit, _ = trace(3, 3, tiles, ((0, 1), (1, 0)))
    assert lit == {(2, 1), (1, 0)}


def test_out_of_bounds_terminates_without_lighting_anything():
    lit, segs = trace(1, 1, {}, ((0, 0), (1, 0)))
    assert lit == set()
    assert segs == [(0, 0, 0.5, 0)]


def test_ccw_is_a_90_degree_rotation():
    assert ccw((1, 0)) == (0, -1)  # R -> U
    assert ccw((0, -1)) == (-1, 0)  # U -> L
    assert ccw((-1, 0)) == (0, 1)  # L -> D
    assert ccw((0, 1)) == (1, 0)  # D -> R


@pytest.mark.parametrize("level_index", range(len(LEVELS)))
def test_level_is_solvable(level_index):
    level = LEVELS[level_index]
    mirrors = level["mirrors"]
    targets = level["targets"]
    fixed = level["fixed"]
    emit = level["emit"]

    solvable = False
    for combo in product("/\\", repeat=len(mirrors)):
        tiles = dict(fixed)
        tiles.update(zip(mirrors, combo))
        lit, _ = trace(level["W"], level["H"], tiles, emit)
        if targets <= lit:
            solvable = True
            break

    assert solvable, f"level {level_index} has no mirror combination that lights every target"
