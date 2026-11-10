"""Pixels as text rows: draw_rows (drawing.py) and read_rows (pixel_read.py)."""
import json

from conftest import ok, run

from aseprite_mcp.tools import canvas, drawing, pixel_read

FACE = ["..KK..", ".KSSK.", "KSSSSK"]
LEGEND = {"K": "#1A1C2C", "S": "#F4B41B"}


def color_at(sprite, x, y, layer):
    return run(pixel_read.get_pixel_color(sprite, x, y, layer, 1)).lower()


def test_draw_rows_places_pixels(sprite):
    ok(run(canvas.add_layer(sprite, "face")))
    result = ok(run(drawing.draw_rows(sprite, "face", 1, 2, 3, FACE, LEGEND)))
    assert "Drew 12 pixels" in result
    assert color_at(sprite, 4, 3, "face").startswith("#1a1c2c")   # row 1, column 3: K
    assert color_at(sprite, 4, 5, "face").startswith("#f4b41b")   # row 3, column 3: S
    assert "a=0" in color_at(sprite, 2, 3, "face"), "'.' must leave the pixel untouched"


def test_read_rows_round_trips(sprite):
    read = json.loads(ok(run(pixel_read.read_rows(sprite, 2, 3, 6, 3, 1, "face"))))
    assert read["rows"] == ["..AA..", ".ABBA.", "ABBBBA"]
    assert read["legend"] == {"A": "#1A1C2C", "B": "#F4B41B"}
    ok(run(canvas.add_layer(sprite, "copy")))
    ok(run(drawing.draw_rows(sprite, "copy", 1, 2, 3, read["rows"], read["legend"])))
    again = json.loads(ok(run(pixel_read.read_rows(sprite, 2, 3, 6, 3, 1, "copy"))))
    assert again["rows"] == read["rows"] and again["legend"] == read["legend"]


def test_read_rows_composites_without_a_layer(sprite):
    # fixture: red 'body' rect from (8,8); the face sits at (2,3) on other layers
    read = json.loads(ok(run(pixel_read.read_rows(sprite, 6, 7, 4, 3))))
    assert read["rows"] == ["....", "..AA", "..AA"]
    assert read["legend"] == {"A": "#D04648"}


def test_draw_rows_rejects_ragged_rows(sprite):
    res = run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["KK", "K", "KK"], LEGEND))
    assert res.startswith("Invalid rows") and "row 2" in res, res


def test_draw_rows_rejects_bad_legend(sprite):
    assert "single characters" in run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["KK"], {"KK": "#000"}))
    assert run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["KK"], {"K": "#GG0000"})).startswith("Invalid")
    assert "nothing to draw" in run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["...."], LEGEND))
    assert "not found" in run(drawing.draw_rows(sprite, "missing", 1, 0, 0, ["K"], LEGEND))


def test_draw_rows_reports_unknown_characters(sprite):
    result = ok(run(drawing.draw_rows(sprite, "face", 1, 0, 20, ["KZK"], LEGEND)))
    assert "'Z' (1 px)" in result
    assert "a=0" in color_at(sprite, 1, 20, "face")


def test_draw_rows_outline_goes_around_the_outside(sprite):
    ok(run(canvas.add_layer(sprite, "dot")))
    result = ok(run(drawing.draw_rows(sprite, "dot", 1, 28, 28, ["S"], LEGEND, "#000000")))
    assert "4 px outline" in result
    for x, y in ((27, 28), (29, 28), (28, 27), (28, 29)):
        assert color_at(sprite, x, y, "dot").startswith("#000000"), (x, y)
    assert "a=0" in color_at(sprite, 27, 27, "dot"), "the outline skips diagonals"


def test_draw_rows_outline_draws_over_existing_pixels(sprite):
    # On a filled layer (a scene) the outline still separates the object.
    ok(run(drawing.draw_rows(sprite, "body", 1, 12, 12, ["S"], LEGEND, "#000000")))
    assert color_at(sprite, 11, 12, "body").startswith("#000000")
    assert color_at(sprite, 12, 12, "body").startswith("#f4b41b")


def test_draw_rows_can_erase(sprite):
    ok(run(drawing.draw_rows(sprite, "body", 1, 20, 20, ["E"], {"E": "#00000000"})))
    assert "a=0" in color_at(sprite, 20, 20, "body")


def test_read_rows_limits(sprite):
    assert "at most" in run(pixel_read.read_rows(sprite, 0, 0, 200, 200))
    assert "must be > 0" in run(pixel_read.read_rows(sprite, 0, 0, 0, 4))
    assert "not found" in run(pixel_read.read_rows(sprite, 0, 0, 4, 4, 1, "missing"))


def test_draw_rows_clip_keeps_paint_inside_the_rectangle(sprite):
    ok(run(canvas.add_layer(sprite, "clipped")))
    result = ok(run(drawing.draw_rows(sprite, "clipped", 1, 0, 0, ["SSSS", "SSSS"], LEGEND, "#000000", True, "1,0,2,2")))
    assert "Drew 4 pixels" in result and "Clipped 4 pixels outside 1,0,2,2" in result
    assert color_at(sprite, 1, 0, "clipped").startswith("#f4b41b")
    assert "a=0" in color_at(sprite, 0, 0, "clipped"), "pixels left of the clip stay untouched"
    assert "a=0" in color_at(sprite, 3, 1, "clipped"), "pixels right of the clip stay untouched"
    assert "a=0" in color_at(sprite, 1, 2, "clipped"), "the outline is clipped too"


def test_draw_rows_rejects_bad_clip(sprite):
    assert run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["K"], LEGEND, None, True, "1,2,3")).startswith("Invalid region")
    assert run(drawing.draw_rows(sprite, "face", 1, 0, 0, ["K"], LEGEND, None, True, "10,10,2,2")).startswith("Invalid clip")
