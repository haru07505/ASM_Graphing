from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from tkinter import colorchooser, messagebox

import customtkinter as ctk

from gui.function_panel import FUNCTION_TYPES, FunctionPanel, format_expression
from gui.graph_canvas import GraphCanvas
from gui.graph_list import GraphList


MAX_GRAPHS = 5
SIDEBAR_WIDTH = 370
DEFAULT_COLORS = ["#2dd4bf", "#f97316", "#a78bfa", "#f43f5e", "#84cc16"]
DLL_ERROR_MESSAGES = {
    -1: "Đã vượt quá giới hạn 5 đồ thị.",
    -2: "ID đồ thị không hợp lệ.",
    -3: "Loại hàm không hợp lệ.",
    -4: "Số lượng hệ số không hợp lệ.",
    -5: "Hệ số phải nằm trong khoảng [-1000; 1000].",
    -7: "Buffer, con trỏ hoặc kích thước không hợp lệ.",
}


class DllUnavailableError(RuntimeError):
    pass


class GraphCoreBridge:
    """ctypes interface to asm/dll/graph_core.dll.

    Python only marshals data and draws returned points. Validation, graph state,
    coordinate conversion, zoom, pan, and point generation are delegated to DLL.
    """

    def __init__(self) -> None:
        self.root_dir = Path(__file__).resolve().parents[1]
        self.dll_path = self.root_dir / "dll" / "graph_core.dll"
        self.available = False
        self.error = ""
        self.lib: ctypes.CDLL | None = None

        try:
            loader = getattr(ctypes, "WinDLL", ctypes.CDLL)
            self.lib = loader(str(self.dll_path))
            self._bind_functions()
            self.available = True
        except OSError as exc:
            self.error = str(exc)
        except AttributeError as exc:
            self.error = f"Missing DLL export: {exc}"

    def _bind_functions(self) -> None:
        assert self.lib is not None

        int_t = ctypes.c_int
        double_t = ctypes.c_double
        double_ptr = ctypes.POINTER(double_t)

        self.lib.add_graph.argtypes = [int_t, double_ptr, int_t, int_t]
        self.lib.add_graph.restype = int_t

        self.lib.edit_graph.argtypes = [int_t, int_t, double_ptr, int_t]
        self.lib.edit_graph.restype = int_t

        self.lib.delete_graph.argtypes = [int_t]
        self.lib.delete_graph.restype = int_t

        self.lib.set_visible.argtypes = [int_t, int_t]
        self.lib.set_visible.restype = int_t

        self.lib.set_color.argtypes = [int_t, int_t]
        self.lib.set_color.restype = int_t

        self.lib.generate_points.argtypes = [int_t, int_t, int_t, double_ptr, int_t]
        self.lib.generate_points.restype = int_t

        self.lib.generate_axis_ticks.argtypes = [int_t, int_t, int_t, double_ptr, int_t]
        self.lib.generate_axis_ticks.restype = int_t

        self.lib.find_nearest_graph_point.argtypes = [
            double_t,
            double_t,
            int_t,
            int_t,
            int_t,
            double_ptr,
        ]
        self.lib.find_nearest_graph_point.restype = int_t

        self.lib.zoom_in.argtypes = []
        self.lib.zoom_in.restype = int_t

        self.lib.zoom_out.argtypes = []
        self.lib.zoom_out.restype = int_t

        self.lib.pan.argtypes = [double_t, double_t]
        self.lib.pan.restype = int_t

        self.lib.reset_view.argtypes = []
        self.lib.reset_view.restype = int_t

        self.lib.screen_to_math.argtypes = [
            double_t,
            double_t,
            int_t,
            int_t,
            double_ptr,
            double_ptr,
        ]
        self.lib.screen_to_math.restype = int_t

        self.lib.math_to_screen.argtypes = [
            double_t,
            double_t,
            int_t,
            int_t,
            double_ptr,
            double_ptr,
        ]
        self.lib.math_to_screen.restype = int_t

        self.lib.get_graph_count.argtypes = []
        self.lib.get_graph_count.restype = int_t

        self.lib.get_zoom_percent.argtypes = []
        self.lib.get_zoom_percent.restype = double_t

        self.lib.get_error_code.argtypes = []
        self.lib.get_error_code.restype = int_t

    def _require(self) -> ctypes.CDLL:
        if not self.available or self.lib is None:
            raise DllUnavailableError(
                f"Chưa tải được DLL: {self.dll_path}. Hãy chạy asm\\build.bat trước."
            )
        return self.lib

    def _check(self, result: int) -> int:
        if result < 0:
            message = DLL_ERROR_MESSAGES.get(result, f"DLL trả về lỗi {result}.")
            raise RuntimeError(message)
        return result

    @staticmethod
    def _coeff_buffer(coefficients: list[float]) -> ctypes.Array[ctypes.c_double]:
        values = (coefficients + [0.0, 0.0, 0.0, 0.0])[:4]
        return (ctypes.c_double * 4)(*values)

    def add_graph(self, function_type: int, coefficients: list[float], color_rgb: int) -> int:
        lib = self._require()
        coeffs = self._coeff_buffer(coefficients)
        return self._check(
            lib.add_graph(function_type, coeffs, len(coefficients), color_rgb)
        )

    def edit_graph(self, graph_id: int, function_type: int, coefficients: list[float]) -> None:
        lib = self._require()
        coeffs = self._coeff_buffer(coefficients)
        self._check(lib.edit_graph(graph_id, function_type, coeffs, len(coefficients)))

    def delete_graph(self, graph_id: int) -> None:
        self._check(self._require().delete_graph(graph_id))

    def set_visible(self, graph_id: int, visible: bool) -> None:
        self._check(self._require().set_visible(graph_id, int(visible)))

    def set_color(self, graph_id: int, color_rgb: int) -> None:
        self._check(self._require().set_color(graph_id, color_rgb))

    def generate_points(
        self, graph_id: int, width: int, height: int, max_pairs: int
    ) -> list[tuple[float, float]]:
        lib = self._require()
        max_pairs = max(0, max_pairs)
        buffer = (ctypes.c_double * (max_pairs * 2))()
        count = self._check(lib.generate_points(graph_id, width, height, buffer, max_pairs))
        return [(buffer[i * 2], buffer[i * 2 + 1]) for i in range(count)]

    def generate_axis_ticks(
        self, axis: int, width: int, height: int, max_pairs: int = 128
    ) -> list[tuple[float, float]]:
        lib = self._require()
        buffer = (ctypes.c_double * (max_pairs * 2))()
        count = self._check(lib.generate_axis_ticks(axis, width, height, buffer, max_pairs))
        return [(buffer[i * 2], buffer[i * 2 + 1]) for i in range(count)]

    def find_nearest_graph_point(
        self,
        graph_id: int,
        screen_x: float,
        screen_y: float,
        width: int,
        height: int,
    ) -> tuple[float, float, float, float] | None:
        lib = self._require()
        buffer = (ctypes.c_double * 4)()
        found = self._check(
            lib.find_nearest_graph_point(screen_x, screen_y, graph_id, width, height, buffer)
        )
        if found == 0:
            return None
        return buffer[0], buffer[1], buffer[2], buffer[3]

    def zoom_in(self) -> None:
        self._check(self._require().zoom_in())

    def zoom_out(self) -> None:
        self._check(self._require().zoom_out())

    def pan(self, dx: float, dy: float) -> None:
        self._check(self._require().pan(dx, dy))

    def reset_view(self) -> None:
        self._check(self._require().reset_view())

    def screen_to_math(
        self, screen_x: float, screen_y: float, width: int, height: int
    ) -> tuple[float, float]:
        lib = self._require()
        out_x = ctypes.c_double()
        out_y = ctypes.c_double()
        self._check(lib.screen_to_math(screen_x, screen_y, width, height, out_x, out_y))
        return out_x.value, out_y.value

    def math_to_screen(
        self, math_x: float, math_y: float, width: int, height: int
    ) -> tuple[float, float]:
        lib = self._require()
        out_x = ctypes.c_double()
        out_y = ctypes.c_double()
        self._check(lib.math_to_screen(math_x, math_y, width, height, out_x, out_y))
        return out_x.value, out_y.value

    def get_graph_count(self) -> int:
        return self._check(self._require().get_graph_count())

    def get_zoom_percent(self) -> float:
        return float(self._require().get_zoom_percent())


@dataclass
class GraphRecord:
    graph_id: int
    function_key: str
    coefficients: list[float]
    color_hex: str
    color_rgb: int
    visible: bool = True

    @property
    def expression(self) -> str:
        return format_expression(self.function_key, self.coefficients)


def hex_to_rgb_int(color: str) -> int:
    value = color.strip().lstrip("#")
    return int(value, 16)


def rgb_tuple_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class GraphingApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("GRAPHING")
        self.geometry("1220x760")
        self.minsize(960, 620)

        self.bridge = GraphCoreBridge()
        self.records: list[GraphRecord] = []
        self.selected_id: int | None = None

        self.status_x = ctk.StringVar(value="X: --")
        self.status_y = ctk.StringVar(value="Y: --")
        self.status_zoom = ctk.StringVar(value="Tỷ lệ: --")
        self.status_count = ctk.StringVar(value="Đồ thị: 0/5")
        self.status_message = ctk.StringVar(value="")

        self._build_layout()
        self._refresh_all()

        if not self.bridge.available:
            self.status_message.set("Chưa có DLL. Chạy asm\\build.bat để tạo dll\\graph_core.dll.")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color="#d5e0ea",
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(1, weight=1)

        self.function_panel = FunctionPanel(
            sidebar,
            on_draw=self._handle_draw_new,
            on_update=self._handle_update,
            on_cancel=self._clear_selection,
        )
        self.function_panel.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))

        self.graph_list = GraphList(
            sidebar,
            on_select=self._select_graph,
            on_visible=self._toggle_visible,
            on_color=self._choose_color,
            on_delete=self._delete_graph,
        )
        self.graph_list.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        self.graph_canvas = GraphCanvas(
            self,
            bridge=self.bridge,
            graph_provider=lambda: list(self.records),
            on_cursor=self._update_cursor,
            on_view_changed=self._refresh_status,
            on_background_click=self._exit_edit_mode,
        )
        self.graph_canvas.grid(row=0, column=1, sticky="nsew")

        status = ctk.CTkFrame(self, corner_radius=0, height=34)
        status.grid(row=1, column=0, columnspan=2, sticky="ew")
        status.grid_columnconfigure(4, weight=1)

        for column, variable in enumerate(
            [self.status_x, self.status_y, self.status_zoom, self.status_count]
        ):
            label = ctk.CTkLabel(status, textvariable=variable, width=110, anchor="w")
            label.grid(row=0, column=column, padx=(12 if column == 0 else 4, 4), pady=4)

        message = ctk.CTkLabel(status, textvariable=self.status_message, anchor="e")
        message.grid(row=0, column=4, sticky="ew", padx=12, pady=4)

    def _handle_draw_new(self, function_key: str, coefficients: list[float]) -> None:
        function_type = FUNCTION_TYPES[function_key]["type_id"]
        try:
            if len(self.records) >= MAX_GRAPHS:
                message = "Đã đạt giới hạn 5 đồ thị."
                messagebox.showwarning("GRAPHING", message)
                self.status_message.set(message)
                return

            color_hex = DEFAULT_COLORS[len(self.records) % len(DEFAULT_COLORS)]
            color_rgb = hex_to_rgb_int(color_hex)
            graph_id = self.bridge.add_graph(function_type, coefficients, color_rgb)
            self.records.append(
                GraphRecord(
                    graph_id=graph_id,
                    function_key=function_key,
                    coefficients=coefficients,
                    color_hex=color_hex,
                    color_rgb=color_rgb,
                )
            )
            self.selected_id = None
            self.function_panel.set_editing(False)
            self.status_message.set("Đã vẽ đồ thị mới.")
        except (DllUnavailableError, RuntimeError) as exc:
            messagebox.showerror("GRAPHING", str(exc))
            self.status_message.set(str(exc))
            return

        self._refresh_all()

    def _handle_update(self, function_key: str, coefficients: list[float]) -> None:
        if self.selected_id is None:
            message = "Hãy chọn một đồ thị để cập nhật."
            messagebox.showwarning("GRAPHING", message)
            self.status_message.set(message)
            return

        function_type = FUNCTION_TYPES[function_key]["type_id"]
        record = self._find_record(self.selected_id)
        if record is None:
            self._clear_selection()
            return

        try:
            self.bridge.edit_graph(record.graph_id, function_type, coefficients)
            record.function_key = function_key
            record.coefficients = coefficients
            self.status_message.set("Đã cập nhật đồ thị.")
        except (DllUnavailableError, RuntimeError) as exc:
            messagebox.showerror("GRAPHING", str(exc))
            self.status_message.set(str(exc))
            return

        self._refresh_all()

    def _select_graph(self, graph_id: int) -> None:
        record = self._find_record(graph_id)
        if record is None:
            return
        self.selected_id = graph_id
        self.function_panel.load_graph(record)
        self.graph_list.set_selected(graph_id)
        self.status_message.set("Đang chỉnh sửa đồ thị đã chọn.")

    def _clear_selection(self) -> None:
        self.selected_id = None
        self.function_panel.clear()
        self.graph_list.set_selected(None)
        self.status_message.set("")

    def _exit_edit_mode(self) -> None:
        if self.selected_id is None:
            return
        self.selected_id = None
        self.function_panel.set_editing(False)
        self.graph_list.set_selected(None)
        self.status_message.set("")

    def _toggle_visible(self, graph_id: int, visible: bool) -> None:
        record = self._find_record(graph_id)
        if record is None:
            return
        try:
            self.bridge.set_visible(graph_id, visible)
            record.visible = visible
            self.status_message.set("Đã cập nhật trạng thái hiển thị.")
        except (DllUnavailableError, RuntimeError) as exc:
            messagebox.showerror("GRAPHING", str(exc))
            self.status_message.set(str(exc))
        self._refresh_all()

    def _choose_color(self, graph_id: int) -> None:
        record = self._find_record(graph_id)
        if record is None:
            return

        picked = colorchooser.askcolor(color=record.color_hex, title="Chọn màu đồ thị")
        if picked[0] is None:
            return

        color_hex = rgb_tuple_to_hex(tuple(int(part) for part in picked[0]))
        color_rgb = hex_to_rgb_int(color_hex)
        try:
            self.bridge.set_color(graph_id, color_rgb)
            record.color_hex = color_hex
            record.color_rgb = color_rgb
            self.status_message.set("Đã đổi màu đồ thị.")
        except (DllUnavailableError, RuntimeError) as exc:
            messagebox.showerror("GRAPHING", str(exc))
            self.status_message.set(str(exc))
        self._refresh_all()

    def _delete_graph(self, graph_id: int) -> None:
        record = self._find_record(graph_id)
        if record is None:
            return

        try:
            self.bridge.delete_graph(graph_id)
            self.records = [item for item in self.records if item.graph_id != graph_id]
            if self.selected_id == graph_id:
                self._clear_selection()
            self.status_message.set("Đã xóa đồ thị.")
        except (DllUnavailableError, RuntimeError) as exc:
            messagebox.showerror("GRAPHING", str(exc))
            self.status_message.set(str(exc))
        self._refresh_all()

    def _find_record(self, graph_id: int) -> GraphRecord | None:
        return next((record for record in self.records if record.graph_id == graph_id), None)

    def _refresh_all(self) -> None:
        self.graph_list.update_records(self.records, self.selected_id)
        self.graph_canvas.redraw()
        self._refresh_status()

    def _refresh_status(self) -> None:
        try:
            zoom = self.bridge.get_zoom_percent()
            count = self.bridge.get_graph_count()
            self.status_zoom.set(f"Tỷ lệ: {zoom:.0f}%")
            self.status_count.set(f"Đồ thị: {count}/{MAX_GRAPHS}")
        except (DllUnavailableError, RuntimeError):
            self.status_zoom.set("Tỷ lệ: --")
            self.status_count.set(f"Đồ thị: {len(self.records)}/{MAX_GRAPHS}")

    def _update_cursor(self, math_x: float | None, math_y: float | None) -> None:
        if math_x is None or math_y is None:
            self.status_x.set("X: --")
            self.status_y.set("Y: --")
            return
        self.status_x.set(f"X: {math_x:.2f}")
        self.status_y.set(f"Y: {math_y:.2f}")
