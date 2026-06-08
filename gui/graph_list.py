from __future__ import annotations

from typing import Callable

import customtkinter as ctk


VISIBLE_ICON = "👁"
DELETE_ICON = "🗑"


class GraphList(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_select: Callable[[int], None],
        on_visible: Callable[[int, bool], None],
        on_color: Callable[[int], None],
        on_delete: Callable[[int], None],
    ) -> None:
        super().__init__(master, corner_radius=8, fg_color="#ffffff")
        self.on_select = on_select
        self.on_visible = on_visible
        self.on_color = on_color
        self.on_delete = on_delete
        self.selected_id: int | None = None
        self.records: list[object] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Danh sách đồ thị",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.container.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self,
            text="Chưa có đồ thị",
            text_color="#64748b",
        )
        self.empty_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

    def update_records(self, records: list[object], selected_id: int | None) -> None:
        self.records = records
        self.selected_id = selected_id

        for child in self.container.winfo_children():
            child.destroy()

        self.empty_label.grid_remove()
        if not records:
            self.empty_label.grid()
            return

        for row_index, record in enumerate(records):
            self._add_row(row_index, record)

    def set_selected(self, graph_id: int | None) -> None:
        self.selected_id = graph_id
        self.update_records(self.records, self.selected_id)

    def _add_row(self, row_index: int, record: object) -> None:
        selected = record.graph_id == self.selected_id
        row = ctk.CTkFrame(
            self.container,
            corner_radius=8,
            fg_color="#dbeafe" if selected else "#f8fafc",
        )
        row.grid(row=row_index, column=0, sticky="ew", pady=5)
        row.grid_columnconfigure(1, weight=1)

        color_button = ctk.CTkButton(
            row,
            text="",
            width=26,
            height=26,
            corner_radius=6,
            fg_color=record.color_hex,
            hover_color=record.color_hex,
            command=lambda graph_id=record.graph_id: self.on_color(graph_id),
        )
        color_button.grid(row=0, column=0, padx=(8, 6), pady=8)

        label = ctk.CTkLabel(
            row,
            text=record.expression,
            anchor="w",
            text_color="#0f172a" if record.visible else "#94a3b8",
        )
        label.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=8)
        label.bind("<Button-1>", lambda _event, graph_id=record.graph_id: self.on_select(graph_id))
        row.bind("<Button-1>", lambda _event, graph_id=record.graph_id: self.on_select(graph_id))

        visible_button = ctk.CTkButton(
            row,
            text=VISIBLE_ICON,
            width=34,
            height=28,
            corner_radius=7,
            fg_color="#dbeafe" if record.visible else "#e5e7eb",
            hover_color="#bfdbfe" if record.visible else "#d1d5db",
            text_color="#2563eb" if record.visible else "#94a3b8",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=15),
            command=lambda graph_id=record.graph_id, visible=record.visible: self.on_visible(
                graph_id, not visible
            ),
        )
        visible_button.grid(row=0, column=2, padx=4, pady=8)

        delete_button = ctk.CTkButton(
            row,
            text=DELETE_ICON,
            width=34,
            height=28,
            corner_radius=7,
            fg_color="#738C98",
            hover_color="#617ca1",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=15),
            command=lambda graph_id=record.graph_id: self.on_delete(graph_id),
        )
        delete_button.grid(row=0, column=3, padx=(4, 8), pady=8)
