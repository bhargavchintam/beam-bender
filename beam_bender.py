"""
Beam Bender (Panda3D).

A small grid puzzle: rotate the mirrors so the emitter's beam reflects across the
board and lights every target. The beam re-traces instantly as you rotate.

Controls: Tab cycles the selected mirror, Space rotates it (/ <-> \\). Solve a
level by lighting every target. R resets the level, Escape quits. Self-contained
- uses only shapes/models that ship with Panda3D, so no external assets needed.
"""

import sys
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import (
    AmbientLight, DirectionalLight, CardMaker, LineSegs, TextNode, NodePath,
    Vec3, Vec4,
)

# ---- beam logic (same rules that were unit-tested) ----
R = (1, 0); L = (-1, 0); D = (0, 1); U = (0, -1)
def ccw(d): x, y = d; return (y, -x)
SLASH = {R: U, U: R, L: D, D: L}
BSLASH = {R: D, D: R, L: U, U: L}


def trace(W, H, tiles, emitter):
    """Return (lit_targets, segments). segments are (x0,y0,x1,y1) in grid cells."""
    start, sd = emitter
    lit = set(); seen = set(); segs = []
    stack = [(start, sd)]
    while stack:
        (x, y), d = stack.pop()
        nx, ny = x + d[0], y + d[1]
        if not (0 <= nx < W and 0 <= ny < H):
            segs.append((x, y, x + d[0] * 0.5, y + d[1] * 0.5)); continue
        if ((nx, ny), d) in seen:
            continue
        seen.add(((nx, ny), d))
        segs.append((x, y, nx, ny))
        t = tiles.get((nx, ny))
        if t == '#':
            continue
        if t == 'T':
            lit.add((nx, ny)); continue
        if t == '/':
            stack.append(((nx, ny), SLASH[d])); continue
        if t == '\\':
            stack.append(((nx, ny), BSLASH[d])); continue
        if t == '+':
            stack.append(((nx, ny), d)); stack.append(((nx, ny), ccw(d))); continue
        stack.append(((nx, ny), d))
    return lit, segs


# ---- levels ----
# Each level: size, emitter (cell,dir), fixed tiles, list of rotatable mirror
# cells (player toggles these between '/' and '\\'), and the target set.
LEVELS = [
    {"W": 6, "H": 6, "emit": ((0, 0), R),
     "fixed": {(0, 5): 'T'}, "mirrors": [(5, 0), (5, 5)], "targets": {(0, 5)}},
    {"W": 6, "H": 6, "emit": ((0, 0), R),
     "fixed": {(3, 0): '#', (5, 0): 'T'},
     "mirrors": [(2, 0), (2, 2), (5, 2)], "targets": {(5, 0)}},
    {"W": 6, "H": 6, "emit": ((0, 0), R),
     "fixed": {(3, 3): '+', (3, 5): 'T', (5, 3): 'T'},
     "mirrors": [(3, 0)], "targets": {(3, 5), (5, 3)}},
]


class BeamBender(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.05, 0.06, 0.10)
        self.disableMouse()
        self.setupLights()
        self.setupCamera()
        self.setupHud()

        self.level_index = 0
        self.boardRoot = None
        self.beamNode = None
        self.loadLevel()

        self.accept("tab", self.cycleSelection)
        self.accept("space", self.rotateSelected)
        self.accept("r", self.resetLevel)
        self.accept("escape", sys.exit)

    def setupLights(self):
        amb = AmbientLight("amb"); amb.setColor((0.5, 0.5, 0.55, 1))
        self.render.setLight(self.render.attachNewNode(amb))
        sun = DirectionalLight("sun"); sun.setColor((0.7, 0.7, 0.7, 1))
        snp = self.render.attachNewNode(sun); snp.setHpr(-50, -60, 0)
        self.render.setLight(snp)

    def setupCamera(self):
        self.camera.setPos(2.5, -9, 12)
        self.camera.lookAt(2.5, 2.5, 0)

    def setupHud(self):
        self.hud = OnscreenText(text="", pos=(-1.3, 0.9), scale=0.06,
                                fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True)
        self.msg = OnscreenText(text="", pos=(0, -0.85), scale=0.08,
                                fg=(0.6, 1, 0.6, 1), align=TextNode.ACenter, mayChange=True)

    # ---- world helpers ----
    def gridToWorld(self, cx, cy):
        return Vec3(cx, (self.H - 1 - cy), 0)   # flip y so row 0 is at the back

    def tile(self, cx, cy, colour, z=0.0, size=0.9):
        cm = CardMaker("tile")
        cm.setFrame(-size / 2, size / 2, -size / 2, size / 2)
        np = self.boardRoot.attachNewNode(cm.generate())
        np.setP(-90)
        np.setPos(self.gridToWorld(cx, cy) + Vec3(0, 0, z))
        np.setColor(*colour)
        return np

    def loadLevel(self):
        if self.boardRoot:
            self.boardRoot.removeNode()
        self.boardRoot = self.render.attachNewNode("board")
        lv = LEVELS[self.level_index]
        self.W, self.H = lv["W"], lv["H"]
        self.emit = lv["emit"]
        self.fixed = dict(lv["fixed"])
        self.targets = set(lv["targets"])
        # rotatable mirrors start as '/'
        self.mirror_cells = list(lv["mirrors"])
        self.mirror_state = {c: '/' for c in self.mirror_cells}
        self.selected = 0

        # floor tiles
        for cx in range(self.W):
            for cy in range(self.H):
                self.tile(cx, cy, (0.12, 0.14, 0.20, 1), z=-0.02)
        # fixed tiles
        for (cx, cy), t in self.fixed.items():
            if t == '#':
                self.tile(cx, cy, (0.34, 0.37, 0.45, 1), z=0.2, size=0.8)
            elif t == 'T':
                self.targetNodes = getattr(self, "targetNodes", {})
            elif t == '+':
                self.tile(cx, cy, (0.65, 0.5, 0.95, 1), z=0.05, size=0.7)
        # emitter
        (ex, ey), _ = self.emit
        self.tile(ex, ey, (0.6, 1.0, 0.6, 1), z=0.05, size=0.7)
        # target markers
        self.targetNodes = {}
        for (cx, cy) in self.targets:
            n = self.loader.loadModel("models/smiley")
            n.setScale(0.35)
            n.reparentTo(self.boardRoot)
            n.setPos(self.gridToWorld(cx, cy) + Vec3(0, 0, 0.35))
            self.targetNodes[(cx, cy)] = n
        self.mirrorNodes = {}
        self.refresh()

    def currentTiles(self):
        tiles = dict(self.fixed)
        for c, s in self.mirror_state.items():
            tiles[c] = s
        return tiles

    def refresh(self):
        # redraw mirrors
        for n in self.mirrorNodes.values():
            n.removeNode()
        self.mirrorNodes = {}
        for i, c in enumerate(self.mirror_cells):
            cm = CardMaker("mirror"); cm.setFrame(-0.45, 0.45, -0.06, 0.06)
            m = self.boardRoot.attachNewNode(cm.generate())
            m.setPos(self.gridToWorld(*c) + Vec3(0, 0, 0.25))
            m.setP(-90)
            m.setH(45 if self.mirror_state[c] == '/' else -45)
            bright = (0.5, 0.85, 1.0, 1) if i == self.selected else (0.3, 0.55, 0.7, 1)
            m.setColor(*bright)
            self.mirrorNodes[c] = m

        # recompute beam
        lit, segs = trace(self.W, self.H, self.currentTiles(), self.emit)
        if self.beamNode:
            self.beamNode.removeNode()
        ls = LineSegs(); ls.setThickness(4); ls.setColor(1, 0.82, 0.25, 1)
        for (x0, y0, x1, y1) in segs:
            a = self.gridToWorld(x0, y0) + Vec3(0, 0, 0.15)
            b = self.gridToWorld(x1, y1) + Vec3(0, 0, 0.15)
            ls.moveTo(a); ls.drawTo(b)
        self.beamNode = self.boardRoot.attachNewNode(ls.create())

        # light targets
        for c, n in self.targetNodes.items():
            n.setColorScale(1, 0.45, 0.4, 1) if c in lit else n.setColorScale(0.3, 0.2, 0.2, 1)

        done = self.targets <= lit
        self.hud.setText("Level %d / %d    Targets lit: %d / %d"
                         % (self.level_index + 1, len(LEVELS), len(self.targets & lit),
                            len(self.targets)))
        if done:
            if self.level_index + 1 < len(LEVELS):
                self.msg.setText("Level solved!  Press Space/Tab to continue.")
                self.solved = True
            else:
                self.msg.setText("All levels solved!  Press R to play again.")
                self.solved = True
        else:
            self.msg.setText(""); self.solved = False

    # ---- input ----
    def cycleSelection(self):
        if getattr(self, "solved", False) and self.level_index + 1 < len(LEVELS):
            self.level_index += 1; self.loadLevel(); return
        if self.mirror_cells:
            self.selected = (self.selected + 1) % len(self.mirror_cells)
            self.refresh()

    def rotateSelected(self):
        if getattr(self, "solved", False) and self.level_index + 1 < len(LEVELS):
            self.level_index += 1; self.loadLevel(); return
        if self.mirror_cells:
            c = self.mirror_cells[self.selected]
            self.mirror_state[c] = '\\' if self.mirror_state[c] == '/' else '/'
            self.refresh()

    def resetLevel(self):
        if getattr(self, "solved", False) and self.level_index + 1 == len(LEVELS):
            self.level_index = 0
        self.loadLevel()


if __name__ == "__main__":
    game = BeamBender()
    game.run()
