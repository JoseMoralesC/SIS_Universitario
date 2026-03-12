from __future__ import annotations

import tkinter as tk


class PopupSlider:
    """
    Animación simple para popups/Toplevel:
    - entrada lateral
    - salida lateral
    - sin autocierre
    """

    def __init__(self, tk_root: tk.Misc):
        self.root = tk_root

    def slide_in(
        self,
        win: tk.Toplevel,
        *,
        w: int,
        h: int,
        x_to: int,
        y: int,
        offset: int = 120,
        step: int = 40,
        delay_ms: int = 8,
        on_done=None,
    ):
        x_from = x_to + offset

        def tick(x: int):
            if x <= x_to:
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

            self.root.after(delay_ms, lambda: tick(x - step))

        tick(x_from)

    def slide_out(
        self,
        win: tk.Toplevel,
        *,
        w: int,
        h: int,
        x_from: int,
        y: int,
        offset: int = 120,
        step: int = 40,
        delay_ms: int = 8,
        on_done=None,
    ):
        x_to = x_from + offset

        def tick(x: int):
            if x >= x_to:
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

            self.root.after(delay_ms, lambda: tick(x + step))

        tick(x_from)