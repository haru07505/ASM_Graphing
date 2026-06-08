from __future__ import annotations

import math
import tkinter as tk
from typing import Callable

import customtkinter as ctk


class GraphCanvas(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        bridge: object,
        graph_provider: Callable[[], list[object]],
        on_cursor: Callable[[float | None, float | None], None],
        on_view_changed: Callable[[], None],
        on_background_click: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color="#f8fafc")
        self.bridge = bridge
        self.graph_provider = graph_provider
        self.on_cursor = on_cursor
        self.on_view_changed = on_view_changed
        self.on_background_click = on_background_click
        self.drag_start: tuple[int, int] | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            background="#ffffff",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        toolbar = ctk.CTkFrame(self, corner_radius=8, fg_color="#e2e8f0")
        toolbar.place(relx=1.0, x=-14, y=14, anchor="ne")

        zoom_in = ctk.CTkButton(toolbar, text="+", width=34, command=self._zoom_in)
        zoom_in.grid(row=0, column=0, padx=(8, 4), pady=8)

        zoom_out = ctk.CTkButton(toolbar, text="-", width=34, command=self._zoom_out)
        zoom_out.grid(row=0, column=1, padx=4, pady=8)

        reset = ctk.CTkButton(toolbar, text="Đặt lại", width=72, command=self._reset)
        reset.grid(row=0, column=2, padx=(4, 8), pady=8)

        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Motion>", self._handle_motion)
        self.canvas.bind("<MouseWheel>", self._handle_wheel)
        self.canvas.bind("<Button-4>", lambda _event: self._zoom_in())
        self.canvas.bind("<Button-5>", lambda _event: self._zoom_out())
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan)
        self.canvas.bind("<ButtonRelease-1>", self._stop_pan)

    def redraw(self) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.canvas.delete("all")

        self._draw_grid(width, height)
        self._draw_graphs(width, height)

    def _draw_grid(self, width: int, height: int) -> None:
        self.canvas.create_rectangle(0, 0, width, height, fill="#ffffff", outline="")

        try:
            left, top = self.bridge.screen_to_math(0.0, 0.0, width, height)
            right, bottom = self.bridge.screen_to_math(float(width), float(height), width, height)
            origin_x, origin_y = self.bridge.math_to_screen(0.0, 0.0, width, height)
        except Exception:
            self._draw_static_grid(width, height)
            self.canvas.create_text(
                width / 2,
                height / 2,
                text="Chạy asm\\build.bat để tạo graph_core.dll",
                fill="#64748b",
                font=("Segoe UI", 14),
            )
            return

        min_x, max_x = min(left, right), max(left, right)
        min_y, max_y = min(bottom, top), max(bottom, top)
        step_x = self._nice_step(max_x - min_x)
        step_y = self._nice_step(max_y - min_y)
        x_labels: list[tuple[float, str]] = []
        y_labels: list[tuple[float, str]] = []

        start_x = math.floor(min_x / step_x) * step_x
        x = start_x
        while x <= max_x + step_x:
            screen_x, _ = self.bridge.math_to_screen(x, 0.0, width, height)
            self.canvas.create_line(screen_x, 0, screen_x, height, fill="#e2e8f0")
            if -40 <= screen_x <= width + 40:
                x_labels.append((screen_x, self._format_axis_value(x)))
            x += step_x

        start_y = math.floor(min_y / step_y) * step_y
        y = start_y
        while y <= max_y + step_y:
            _, screen_y = self.bridge.math_to_screen(0.0, y, width, height)
            self.canvas.create_line(0, screen_y, width, screen_y, fill="#e2e8f0")
            if -30 <= screen_y <= height + 30 and abs(y) > step_y * 0.001:
                y_labels.append((screen_y, self._format_axis_value(y)))
            y += step_y

        self.canvas.create_line(origin_x, 0, origin_x, height, fill="#475569", width=2)
        self.canvas.create_line(0, origin_y, width, origin_y, fill="#475569", width=2)

        x_label_y = self._axis_x_label_y(origin_y, height)
        for screen_x, text in x_labels:
            label_x = self._clamp(screen_x, 18, width - 18)
            self.canvas.create_text(
                label_x,
                x_label_y,
                text=text,
                fill="#64748b",
                font=("Segoe UI", 9),
            )

        y_label_x = self._axis_y_label_x(origin_x, width)
        for screen_y, text in y_labels:
            label_y = self._clamp(screen_y, 10, height - 10)
            self.canvas.create_text(
                y_label_x,
                label_y,
                text=text,
                fill="#64748b",
                font=("Segoe UI", 9),
                anchor="e" if y_label_x <= origin_x else "w",
            )

    def _draw_static_grid(self, width: int, height: int) -> None:
        for x in range(0, width, 50):
            self.canvas.create_line(x, 0, x, height, fill="#e2e8f0")
        for y in range(0, height, 50):
            self.canvas.create_line(0, y, width, y, fill="#e2e8f0")
        self.canvas.create_line(width / 2, 0, width / 2, height, fill="#475569", width=2)
        self.canvas.create_line(0, height / 2, width, height / 2, fill="#475569", width=2)

    def _draw_graphs(self, width: int, height: int) -> None:
        for record in self.graph_provider():
            if not record.visible:
                continue
            try:
                points = self.bridge.generate_points(record.graph_id, width, height, width)
            except Exception:
                return
            if len(points) < 2:
                continue
            flattened = [coordinate for point in points for coordinate in point]
            line_tag = f"graph_line_{record.graph_id}"
            line_id = self.canvas.create_line(
                *flattened,
                fill=record.color_hex,
                width=2,
                smooth=True,
                activewidth=4,
                tags=(line_tag, "graph_line"),
            )
            self.canvas.tag_bind(
                line_tag,
                "<Enter>",
                lambda event, item_id=line_id, graph=record: self._handle_graph_enter(
                    event, item_id, graph
                ),
            )
            self.canvas.tag_bind(
                line_tag,
                "<Motion>",
                lambda event, graph=record: self._draw_graph_hover(event, graph),
            )
            self.canvas.tag_bind(
                line_tag,
                "<Leave>",
                lambda _event, item_id=line_id: self._handle_graph_leave(item_id),
            )

    def _handle_motion(self, event: tk.Event) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        try:
            math_x, math_y = self.bridge.screen_to_math(
                float(event.x), float(event.y), width, height
            )
            self.on_cursor(math_x, math_y)
            self._draw_cursor_overlay(event.x, event.y, math_x, math_y, width, height)
        except Exception:
            self.on_cursor(None, None)
            self.canvas.delete("cursor")

    def _handle_wheel(self, event: tk.Event) -> None:
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _zoom_in(self) -> None:
        try:
            self.bridge.zoom_in()
        except Exception:
            return
        self.redraw()
        self.on_view_changed()

    def _zoom_out(self) -> None:
        try:
            self.bridge.zoom_out()
        except Exception:
            return
        self.redraw()
        self.on_view_changed()

    def _reset(self) -> None:
        try:
            self.bridge.reset_view()
        except Exception:
            return
        self.redraw()
        self.on_view_changed()

    def _start_pan(self, event: tk.Event) -> None:
        if self.on_background_click is not None:
            self.on_background_click()
        self.drag_start = (event.x, event.y)

    def _pan(self, event: tk.Event) -> None:
        if self.drag_start is None:
            return
        last_x, last_y = self.drag_start
        dx = event.x - last_x
        dy = event.y - last_y
        self.drag_start = (event.x, event.y)

        try:
            self.bridge.pan(float(dx), float(dy))
        except Exception:
            return
        self.redraw()
        self.on_view_changed()

    def _stop_pan(self, _event: tk.Event) -> None:
        self.drag_start = None

    def _draw_cursor_overlay(
        self,
        screen_x: int,
        screen_y: int,
        math_x: float,
        math_y: float,
        width: int,
        height: int,
    ) -> None:
        self.canvas.delete("cursor")
        label = f"({math_x:.2f}, {math_y:.2f})"
        label_width = max(78, len(label) * 7 + 14)
        label_height = 24
        x0 = screen_x + 12
        y0 = screen_y + 12

        if x0 + label_width > width - 8:
            x0 = screen_x - label_width - 12
        if y0 + label_height > height - 8:
            y0 = screen_y - label_height - 12

        x0 = self._clamp(x0, 8, max(8, width - label_width - 8))
        y0 = self._clamp(y0, 8, max(8, height - label_height - 8))
        x1 = x0 + label_width
        y1 = y0 + label_height

        self.canvas.create_line(
            screen_x,
            0,
            screen_x,
            height,
            fill="#bfdbfe",
            dash=(4, 4),
            tags=("cursor",),
            state="disabled",
        )
        self.canvas.create_line(
            0,
            screen_y,
            width,
            screen_y,
            fill="#bfdbfe",
            dash=(4, 4),
            tags=("cursor",),
            state="disabled",
        )
        self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill="#eff6ff",
            outline="#93c5fd",
            tags=("cursor",),
            state="disabled",
        )
        self.canvas.create_text(
            x0 + 8,
            y0 + label_height / 2,
            text=label,
            fill="#0f172a",
            anchor="w",
            font=("Segoe UI", 9),
            tags=("cursor",),
            state="disabled",
        )
        self.canvas.tag_raise("cursor")
        self.canvas.tag_raise("graph_hover")

    def _handle_graph_enter(self, event: tk.Event, item_id: int, record: object) -> None:
        try:
            self.canvas.itemconfigure(item_id, width=4)
        except tk.TclError:
            return
        self._draw_graph_hover(event, record)

    def _handle_graph_leave(self, item_id: int) -> None:
        try:
            self.canvas.itemconfigure(item_id, width=2)
        except tk.TclError:
            pass
        self.canvas.delete("graph_hover")

    def _draw_graph_hover(self, event: tk.Event, record: object) -> None:
        self.canvas.delete("graph_hover")
        label = record.expression
        label_width = max(120, len(label) * 7 + 16)
        label_height = 26
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        x0 = event.x + 14
        y0 = event.y - label_height - 10

        if x0 + label_width > width - 8:
            x0 = event.x - label_width - 14
        if y0 < 8:
            y0 = event.y + 14

        x0 = self._clamp(x0, 8, max(8, width - label_width - 8))
        y0 = self._clamp(y0, 8, max(8, height - label_height - 8))
        x1 = x0 + label_width
        y1 = y0 + label_height

        self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill="#ffffff",
            outline="#cbd5e1",
            tags=("graph_hover",),
            state="disabled",
        )
        self.canvas.create_text(
            x0 + 8,
            y0 + label_height / 2,
            text=label,
            fill="#0f172a",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            tags=("graph_hover",),
            state="disabled",
        )
        self.canvas.tag_raise("graph_hover")

    @staticmethod
    def _axis_x_label_y(origin_y: float, height: int) -> float:
        if 18 <= origin_y <= height - 28:
            return origin_y + 16
        return height - 14

    @staticmethod
    def _axis_y_label_x(origin_x: float, width: int) -> float:
        if 46 <= origin_x <= width - 46:
            return origin_x + 10
        return 36

    @staticmethod
    def _format_axis_value(value: float) -> str:
        if abs(value) < 0.005:
            value = 0.0
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text if text else "0"

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return min(max(value, minimum), maximum)

    @staticmethod
    def _nice_step(span: float) -> float:
        if span <= 0:
            return 1.0
        raw = span / 12.0
        magnitude = 10 ** math.floor(math.log10(raw))
        normalized = raw / magnitude
        if normalized < 2:
            return magnitude
        if normalized < 5:
            return 2 * magnitude
        return 5 * magnitude
