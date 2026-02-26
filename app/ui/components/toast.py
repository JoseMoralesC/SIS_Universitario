# app/ui/components/toast.py
from __future__ import annotations

import tkinter as tk

from app.ui.transitions.window_slide import WindowSlider


class Toast(tk.Toplevel):
    """
    Toast con animación EXACTA tipo WindowSlider (misma lógica geometry+after).
    - Solo anima en X (igual que WindowSlider.slide()).
    - Entra desde right/left hasta el centro.
    - Sale hacia right/left y luego destroy.
    - Clamp para evitar quedar fuera de pantalla (multi-monitor).
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        duration_ms: int = 6000,
        width: int = 520,
        bg: str = "#0f1c2a",
        y_offset: int = -60,
        wrap_pad: int = 40,
        margin: int = 12,
        # ---- animación (igual WindowSlider) ----
        animate: bool = True,
        step: int = 90,
        delay_ms: int = 6,
        slide_in_from: str = "right",   # "right" | "left"
        slide_out_to: str = "right",    # "right" | "left"
        slide_extra_px: int = 180,      # cuánto “afuera” inicia/termina
    ):
        super().__init__(parent)

        self._parent = parent
        self._bg = bg
        self._width = int(width)
        self._y_offset = int(y_offset)
        self._margin = int(margin)

        self._animate = bool(animate)
        self._step = int(step)
        self._delay_ms = int(delay_ms)
        self._slide_in_from = str(slide_in_from)
        self._slide_out_to = str(slide_out_to)
        self._slide_extra_px = int(slide_extra_px)

        self._closing = False
        self._auto_close_after_id: str | None = None
        self._bind_id = None

        # ventana toast
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=bg)

        # --- UI ---
        container = tk.Frame(
            self,
            bg=bg,
            bd=0,
            highlightthickness=1,
            highlightbackground="#223142",
        )
        container.pack(fill="both", expand=True)

        header = tk.Frame(container, bg=bg)
        header.pack(fill="x", padx=14, pady=(12, 6))

        tk.Label(
            header,
            text=title,
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=bg,
        ).pack(side="left", anchor="w")

        tk.Button(
            header,
            text="✕",
            command=self.close,
            bg=bg,
            fg="white",
            bd=0,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            activebackground=bg,
            activeforeground="white",
        ).pack(side="right")

        tk.Label(
            container,
            text=message,
            font=("Segoe UI", 11),
            fg="white",
            bg=bg,
            justify="left",
            wraplength=max(200, self._width - int(wrap_pad)),
        ).pack(fill="both", expand=True, padx=16, pady=(4, 12))

        # medir y fijar tamaño
        self.update_idletasks()
        h = max(80, container.winfo_reqheight())
        self.geometry(f"{self._width}x{h}")

        # target (centro clamp)
        self._target_x, self._target_y = self._calc_target_xy()

        # colocar inicialmente fuera (para animar entrada)
        w = self._width
        x_from = self._x_offscreen_for_side(self._slide_in_from, w, self._target_x)
        try:
            self.geometry(f"{w}x{h}+{x_from}+{self._target_y}")
        except Exception:
            pass

        # seguir al parent si se mueve (opcional, pero útil)
        try:
            top = self._get_top()
            self._bind_id = top.bind("<Configure>", self._on_top_configure, add="+")
        except Exception:
            self._bind_id = None

        # animación entrada (EXACTA WindowSlider)
        if self._animate:
            self.after(1, self._slide_in)
        else:
            self._position_center_safe()

        # autocierre (animado)
        self._auto_close_after_id = self.after(duration_ms, self.close)

    # -----------------------------
    # Helpers posicion
    # -----------------------------
    def _get_top(self) -> tk.Misc:
        try:
            return self._parent.winfo_toplevel()
        except Exception:
            return self.master.winfo_toplevel()

    def _on_top_configure(self, _evt=None):
        if not self.winfo_exists() or self._closing:
            return
        # recalcula target y re-clampa
        self._target_x, self._target_y = self._calc_target_xy()
        if not self._animate:
            self._position_center_safe()

    def _calc_target_xy(self) -> tuple[int, int]:
        top = self._get_top()
        top.update_idletasks()
        self.update_idletasks()

        tw = max(1, top.winfo_width())
        th = max(1, top.winfo_height())
        tx = top.winfo_rootx()
        ty = top.winfo_rooty()

        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())

        x = tx + (tw // 2) - (w // 2)
        y = ty + (th // 2) - (h // 2) + self._y_offset

        # clamp a pantalla actual
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        m = self._margin

        x = max(m, min(int(x), sw - w - m))
        y = max(m, min(int(y), sh - h - m))

        return int(x), int(y)

    def _position_center_safe(self):
        self._target_x, self._target_y = self._calc_target_xy()
        try:
            self.geometry(f"+{self._target_x}+{self._target_y}")
        except Exception:
            pass

    def _x_offscreen_for_side(self, side: str, w: int, x_target: int) -> int:
        """
        Calcula un x fuera de pantalla (sin depender del monitor), para slide horizontal.
        """
        side = (side or "right").lower()
        sw = self.winfo_screenwidth()
        extra = self._slide_extra_px

        if side == "left":
            # completamente fuera por la izquierda
            return -w - extra
        # right (default): fuera por la derecha
        return sw + extra

    # -----------------------------
    # Animación EXACTA WindowSlider
    # -----------------------------
    def _slide_in(self):
        if not self.winfo_exists():
            return

        self._target_x, self._target_y = self._calc_target_xy()
        w = self._width
        h = self.winfo_height()

        x_from = self._x_offscreen_for_side(self._slide_in_from, w, self._target_x)
        x_to = self._target_x
        y = self._target_y

        slider = WindowSlider(self._get_top())
        slider.slide(
            win=self,
            w=w,
            h=h,
            x_from=int(x_from),
            x_to=int(x_to),
            y=int(y),
            step=self._step,
            delay_ms=self._delay_ms,
        )

    def _slide_out(self, on_done=None):
        if not self.winfo_exists():
            if callable(on_done):
                on_done()
            return

        # usa posición actual como origen, para que sea natural
        w = self._width
        h = self.winfo_height()
        x_from = self.winfo_x()

        # destino offscreen
        x_to = self._x_offscreen_for_side(self._slide_out_to, w, self._target_x)
        y = self.winfo_y()

        slider = WindowSlider(self._get_top())
        slider.slide(
            win=self,
            w=w,
            h=h,
            x_from=int(x_from),
            x_to=int(x_to),
            y=int(y),
            step=self._step,
            delay_ms=self._delay_ms,
            on_done=on_done,
        )

    # -----------------------------
    # Close / destroy
    # -----------------------------
    def close(self):
        if self._closing:
            return
        self._closing = True

        # cancelar autocierre si sigue pendiente
        try:
            if self._auto_close_after_id is not None:
                self.after_cancel(self._auto_close_after_id)
        except Exception:
            pass
        self._auto_close_after_id = None

        if self._animate:
            self._slide_out(on_done=self.destroy)
        else:
            self.destroy()

    def destroy(self):
        try:
            if self._bind_id is not None:
                top = self._get_top()
                top.unbind("<Configure>", self._bind_id)
        except Exception:
            pass
        return super().destroy()