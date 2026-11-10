"""Region operation tools (selection.py)."""
from conftest import ok, run

from aseprite_mcp.tools import canvas, drawing, pixel_read, selection


def test_copy_region(sprite):
    ok(run(selection.copy_region(sprite, "body", 1, 8, 8, 8, 8, 20, 20)))


def test_move_region(sprite):
    ok(run(selection.move_region(sprite, "body", 1, 20, 20, 8, 8, 0, 0)))


def test_erase_region(sprite):
    ok(run(selection.erase_region(sprite, "body", 1, 0, 0, 4, 4)))


def test_erase_color(sprite):
    result = ok(run(selection.erase_color(sprite, "body", 1, "#D04648", 0)))
    assert "Erased" in result


def test_clip_to_mask_erases_paint_outside_the_mask(sprite):
    def alpha_zero(x, y):
        return "a=0" in run(pixel_read.get_pixel_color(sprite, x, y, "paint", 1))

    ok(run(canvas.add_layer(sprite, "mask")))
    ok(run(drawing.draw_rectangle_at(sprite, "mask", 1, 2, 2, 4, 4, "#FFFFFF", True)))
    ok(run(canvas.add_layer(sprite, "paint")))
    ok(run(drawing.draw_rectangle_at(sprite, "paint", 1, 0, 0, 8, 8, "#3050A0", True)))

    result = ok(run(selection.clip_to_mask(sprite, "paint", "mask")))
    assert "Erased 48 pixels" in result, result
    assert not alpha_zero(2, 2) and not alpha_zero(5, 5)
    assert alpha_zero(1, 2) and alpha_zero(6, 5) and alpha_zero(0, 0)


def test_clip_to_mask_rejects_bad_input(sprite):
    assert "Mask layer not found" in run(selection.clip_to_mask(sprite, "paint", "missing"))
    assert "Layer not found" in run(selection.clip_to_mask(sprite, "missing", "mask"))
    assert "out of range" in run(selection.clip_to_mask(sprite, "paint", "mask", 9))
