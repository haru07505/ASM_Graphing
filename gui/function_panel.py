from __future__ import annotations

from tkinter import messagebox
from typing import Callable

import customtkinter as ctk


FUNCTION_TYPES = {
    "linear": {
        "type_id": 0,
        "label": "Hàm bậc nhất: y = ax + b",
        "coefficients": ["a", "b"],
    },
    "quadratic": {
        "type_id": 1,
        "label": "Hàm bậc hai: y = ax^2 + bx + c",
        "coefficients": ["a", "b", "c"],
    },
    "sin": {
        "type_id": 2,
        "label": "Hàm sin: y = a*sin(bx + c) + d",
        "coefficients": ["a", "b", "c", "d"],
    },
    "cos": {
        "type_id": 3,
        "label": "Hàm cos: y = a*cos(bx + c) + d",
        "coefficients": ["a", "b", "c", "d"],
    },
}


def format_number(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text else "0"


def format_expression(function_key: str, coefficients: list[float]) -> str:
    values = [format_number(value) for value in coefficients]
    while len(values) < 4:
        values.append("0")

    if function_key == "linear":
        return f"y = {values[0]}x + {values[1]}"
    if function_key == "quadratic":
        return f"y = {values[0]}x^2 + {values[1]}x + {values[2]}"
    if function_key == "sin":
        return f"y = {values[0]}sin({values[1]}x + {values[2]}) + {values[3]}"
    if function_key == "cos":
        return f"y = {values[0]}cos({values[1]}x + {values[2]}) + {values[3]}"
    return "y = ?"


class FunctionPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_draw: Callable[[str, list[float]], None],
        on_update: Callable[[str, list[float]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=8, fg_color="#ffffff")
        self.on_draw = on_draw
        self.on_update = on_update
        self.on_cancel = on_cancel
        self.function_key = ctk.StringVar(value="linear")
        self.entries: dict[str, ctk.CTkEntry] = {}

        self.grid_columnconfigure(0, weight=1)
        self._build()
        self._render_coefficient_inputs()

    def _build(self) -> None:
        title = ctk.CTkLabel(self, text="Nhập hàm số", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        labels = [item["label"] for item in FUNCTION_TYPES.values()]
        self.key_by_label = {
            item["label"]: key for key, item in FUNCTION_TYPES.items()
        }
        self.label_by_key = {
            key: item["label"] for key, item in FUNCTION_TYPES.items()
        }

        self.function_combo = ctk.CTkOptionMenu(
            self,
            values=labels,
            command=self._on_function_change,
            height=36,
            corner_radius=14,
            fg_color="#a4b8c9",
            button_color="#8995ad",
            button_hover_color="#78829f",
            dropdown_fg_color="#e3f0f1",
            dropdown_hover_color="#dbeafe",
            dropdown_text_color="#0f172a",
            text_color="#0f172a",
            font=ctk.CTkFont(size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.function_combo.set(self.label_by_key[self.function_key.get()])
        self.function_combo.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.coefficient_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.coefficient_frame.grid(row=2, column=0, sticky="ew", padx=14)
        self.coefficient_frame.grid_columnconfigure((0, 1), weight=1)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=14, pady=(12, 14))
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        draw_button = ctk.CTkButton(actions, text="Vẽ mới", command=self._draw_new)
        draw_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.update_button = ctk.CTkButton(
            actions,
            text="Cập nhật",
            command=self._update_selected,
            state="disabled",
        )
        self.update_button.grid(row=0, column=1, sticky="ew", padx=5)

        cancel_button = ctk.CTkButton(
            actions,
            text="Hủy",
            command=self._cancel,
            fg_color="#64748b",
            hover_color="#475569",
        )
        cancel_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))

    def _on_function_change(self, label: str) -> None:
        self.function_key.set(self.key_by_label[label])
        self._render_coefficient_inputs()

    def _render_coefficient_inputs(self) -> None:
        for child in self.coefficient_frame.winfo_children():
            child.destroy()
        self.entries.clear()

        coefficient_names = FUNCTION_TYPES[self.function_key.get()]["coefficients"]
        for index, name in enumerate(coefficient_names):
            label = ctk.CTkLabel(self.coefficient_frame, text=name, anchor="w")
            label.grid(row=index, column=0, sticky="w", pady=(0, 6))

            entry = ctk.CTkEntry(
                self.coefficient_frame,
                height=30,
                placeholder_text=f"Hệ số {name}",
            )
            entry.insert(0, "1" if name == "a" else "0")
            entry.grid(row=index, column=1, sticky="ew", pady=(0, 6))
            self.entries[name] = entry

    def _read_coefficients(self) -> list[float] | None:
        coefficients: list[float] = []
        try:
            for name in FUNCTION_TYPES[self.function_key.get()]["coefficients"]:
                coefficients.append(float(self.entries[name].get().strip()))
        except ValueError:
            messagebox.showerror("GRAPHING", "Hệ số phải là số hợp lệ.")
            return None

        return coefficients

    def _draw_new(self) -> None:
        coefficients = self._read_coefficients()
        if coefficients is None:
            return
        self.on_draw(self.function_key.get(), coefficients)

    def _update_selected(self) -> None:
        coefficients = self._read_coefficients()
        if coefficients is None:
            return
        self.on_update(self.function_key.get(), coefficients)

    def _cancel(self) -> None:
        self.clear()
        self.on_cancel()

    def clear(self) -> None:
        self.function_key.set("linear")
        self.function_combo.set(self.label_by_key["linear"])
        self._render_coefficient_inputs()
        self.set_editing(False)

    def set_editing(self, is_editing: bool) -> None:
        self.update_button.configure(state="normal" if is_editing else "disabled")

    def load_graph(self, record: object) -> None:
        self.function_key.set(record.function_key)
        self.function_combo.set(self.label_by_key[record.function_key])
        self._render_coefficient_inputs()

        coefficient_names = FUNCTION_TYPES[record.function_key]["coefficients"]
        for name, value in zip(coefficient_names, record.coefficients):
            entry = self.entries[name]
            entry.delete(0, "end")
            entry.insert(0, format_number(value))
        self.set_editing(True)
