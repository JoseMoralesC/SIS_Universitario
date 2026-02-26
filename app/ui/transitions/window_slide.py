# app/ui/transitions/window_slide.py
from __future__ import annotations
import tkinter as tk


class WindowSlider:
    """
    Animación simple y estable para Toplevel usando geometry.
    Evita parpadeos secuenciando updates con after.
    """
    def __init__(self, tk_root: tk.Misc):
        self.root = tk_root

    def slide(self, win: tk.Toplevel, w: int, h: int, x_from: int, x_to: int, y: int = 0,
              step: int = 90, delay_ms: int = 6, on_done=None):
        direction = 1 if x_to > x_from else -1

        def tick(x: int):
            done = (direction == 1 and x >= x_to) or (direction == -1 and x <= x_to)
            if done:
                try:
                    win.geometry(f"{w}x{h}+{x_to}+{y}")
                except Exception:
                    pass
                if on_done:
                    on_done()
                return

            try:
                win.geometry(f"{w}x{h}+{x}+{y}")
            except Exception:
                pass

            self.root.after(delay_ms, lambda: tick(x + step * direction))

        tick(x_from)