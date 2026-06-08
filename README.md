# GRAPHING

## 1. Tổng quan

**GRAPHING** là đồ án vận dụng Hợp ngữ vào xây dựng ứng dụng vẽ đồ thị toán học cơ bản.

Đồ án là tách rõ vai trò giữa giao diện và xử lý:

- **Python** dùng `CustomTkinter` để xây dựng giao diện người dùng.
- **Canvas** của Tkinter dùng để hiển thị hệ trục tọa độ, lưới và các đường đồ thị.
- **Assembly x86-64 NASM** đảm nhiệm logic xử lý chính.
- Assembly được biên dịch thành file DLL.
- Python gọi các hàm trong DLL thông qua `ctypes`.

Python không trực tiếp xử lý thuật toán đồ thị. Các thao tác như quản lý đồ thị, sinh điểm, zoom, pan và chuyển đổi tọa độ được thiết kế để thực hiện trong DLL Assembly.

## 2. Chức năng

Ứng dụng hỗ trợ các loại hàm số:

- `y = ax + b`
- `y = ax^2 + bx + c`
- `y = a*sin(bx + c) + d`
- `y = a*cos(bx + c) + d`

Các chức năng quản lý đồ thị:

- Thêm đồ thị.
- Chỉnh sửa đồ thị.
- Xóa đồ thị.
- Ẩn hoặc hiện đồ thị.
- Đổi màu đồ thị.
- Quản lý tối đa 5 đồ thị cùng lúc.

Các chức năng tương tác với vùng vẽ:

- Phóng to bằng nút `+` hoặc con lăn chuột.
- Thu nhỏ bằng nút `-` hoặc con lăn chuột.
- Kéo chuột để pan vùng nhìn.
- Reset vùng nhìn về trạng thái ban đầu.
- Hiển thị tọa độ chuột theo hệ tọa độ toán học.
- Hiển thị mức zoom hiện tại.
- Hiển thị số lượng đồ thị đang được quản lý.

Các ràng buộc dữ liệu:

- Tối đa 5 đồ thị.
- Hệ số nằm trong khoảng `[-1000; 1000]`.
- Zoom tối thiểu `10%`.
- Zoom tối đa `1000%`.
- Tọa độ hiển thị tối đa 2 chữ số sau dấu thập phân.

## 3. Kiến trúc

Cấu trúc thư mục của project:

```text
Graphing/
├── main.py
├── gui/
│   ├── app.py
│   ├── graph_canvas.py
│   ├── function_panel.py
│   └── graph_list.py
├── asm/
│   ├── graph_core.asm
│   ├── graph_math.asm
│   ├── graph_manager.asm
│   ├── graph_view.asm
│   ├── graph_core.def
│   └── build.bat
├── dll/
│   └── graph_core.dll
└── README.md
```

Luồng hoạt động chính:

```text
Người dùng
   ↓
Giao diện Python CustomTkinter
   ↓
ctypes
   ↓
graph_core.dll
   ↓
Assembly x86-64 xử lý logic
   ↓
Trả kết quả về Python
   ↓
Canvas hiển thị đồ thị
```

Các hàm DLL được thiết kế để Python gọi:

```c
int graphing_abi_version(void);
int get_error_code(void);
int get_graph_count(void);

int add_graph(int type, double* coeffs, int coeff_count, int color_rgb);
int edit_graph(int id, int type, double* coeffs, int coeff_count);
int delete_graph(int id);
int set_visible(int id, int visible);
int set_color(int id, int color_rgb);

int generate_points(int id, int width, int height, double* out_xy, int max_pairs);
int generate_axis_ticks(int axis, int width, int height, double* out_pairs, int max_pairs);
int find_nearest_graph_point(double sx, double sy, int id, int width, int height, double* out_values);

int zoom_in(void);
int zoom_out(void);
int pan(double dx, double dy);
int reset_view(void);

int screen_to_math(double sx, double sy, int width, int height, double* out_x, double* out_y);
int math_to_screen(double x, double y, int width, int height, double* out_x, double* out_y);
double get_zoom_percent(void);
```

## 4. Giải thích từng phần

### `main.py`

Đây là file khởi động chương trình. File này tạo đối tượng ứng dụng `GraphingApp` và chạy vòng lặp giao diện bằng `mainloop()`.

### `gui/app.py`

Đây là file điều phối chính của giao diện.

File này có các nhiệm vụ:

- Tạo cửa sổ chính.
- Tạo bố cục giao diện gồm panel nhập hàm, danh sách đồ thị, vùng Canvas và thanh trạng thái.
- Tạo lớp `GraphCoreBridge` để kết nối Python với DLL Assembly thông qua `ctypes`.
- Gọi các hàm DLL như `add_graph`, `edit_graph`, `delete_graph`, `generate_points`, `generate_axis_ticks`, `find_nearest_graph_point`, `zoom_in`, `pan`, `reset_view`.
- Cập nhật dữ liệu hiển thị trên giao diện.

### `gui/function_panel.py`

File này xây dựng khu vực nhập dữ liệu hàm số.

Chức năng chính:

- Combobox chọn loại hàm.
- Tự động hiển thị số lượng hệ số phù hợp với từng loại hàm.
- Nhận dữ liệu người dùng nhập.
- Gửi dữ liệu về `app.py` để gọi DLL xử lý.
- Hiển thị biểu thức hàm ở dạng dễ đọc.

### `gui/graph_list.py`

File này xây dựng khu vực quản lý danh sách đồ thị.

Mỗi đồ thị trong danh sách có:

- Tên hoặc biểu thức hàm số.
- Màu đồ thị.
- Checkbox ẩn hoặc hiện.
- Nút xóa.

Người dùng có thể chọn một đồ thị trong danh sách để chỉnh sửa.

### `gui/graph_canvas.py`

File này xây dựng vùng vẽ đồ thị.

Chức năng chính:

- Vẽ nền, lưới tọa độ và hệ trục Oxy.
- Gọi DLL để chuyển đổi tọa độ.
- Gọi DLL để lấy vị trí và giá trị các vạch chia trục.
- Gọi DLL để sinh tập điểm đồ thị.
- Gọi DLL để tìm điểm trên đồ thị gần con trỏ chuột khi hover.
- Vẽ các điểm trả về từ DLL lên Canvas.
- Bắt sự kiện chuột để zoom, pan và cập nhật tọa độ con trỏ.

Python chỉ vẽ dữ liệu đã nhận được, không tự tính toán đồ thị.

### `asm/graph_core.asm`

File này chứa các hàm lõi chung của DLL.

Hiện tại có hàm:

```asm
graphing_abi_version
```

Hàm này trả về phiên bản giao tiếp nhị phân của DLL. Python có thể dùng hàm này để kiểm tra DLL có đúng phiên bản mong muốn hay không.

### `asm/graph_math.asm`

File này chứa phần xử lý toán học.

Chức năng chính:

- Kiểm tra loại hàm.
- Kiểm tra số lượng hệ số.
- Kiểm tra miền giá trị hệ số.
- Tính giá trị `y` từ `x` theo từng loại hàm.

Các hàm lượng giác `sin` và `cos` được đặt ở phía Assembly để đúng yêu cầu đồ án.

### `asm/graph_manager.asm`

File này quản lý danh sách đồ thị trong DLL.

Chức năng chính:

- Lưu trạng thái tối đa 5 đồ thị.
- Thêm đồ thị.
- Sửa đồ thị.
- Xóa đồ thị.
- Bật hoặc tắt hiển thị.
- Đổi màu đồ thị.
- Lưu mã lỗi gần nhất.

### `asm/graph_view.asm`

File này xử lý vùng nhìn và tọa độ.

Chức năng chính:

- Sinh tập điểm đồ thị để Python vẽ lên Canvas.
- Sinh vị trí và giá trị các vạch chia trục tọa độ.
- Tìm điểm trên đồ thị gần con trỏ chuột để hỗ trợ hover.
- Chuyển tọa độ màn hình sang tọa độ toán học.
- Chuyển tọa độ toán học sang tọa độ màn hình.
- Zoom in.
- Zoom out.
- Pan.
- Reset view.
- Trả về mức zoom hiện tại.

### `asm/graph_core.def`

Đây là file khai báo export của DLL.

File này cho linker biết những hàm nào sẽ được công khai để Python có thể gọi bằng `ctypes`.

Ví dụ:

```def
EXPORTS
    add_graph
    edit_graph
    delete_graph
    generate_points
    zoom_in
    zoom_out
```

Nếu một hàm Assembly không nằm trong danh sách `EXPORTS`, Python sẽ không nên gọi trực tiếp hàm đó.

### `asm/build.bat`

File này dùng để build DLL.

Quy trình build:

1. Dùng NASM biên dịch các file `.asm` thành `.obj`.
2. Dùng MinGW-w64 `gcc` link các file `.obj` thành `graph_core.dll`.
3. Đặt DLL sau khi build vào thư mục `dll/`.
4. Xóa các file `.obj` trung gian sau khi build thành công.

### `dll/graph_core.dll`

Đây là file DLL được tạo sau khi chạy `asm/build.bat`.

Python sẽ load DLL này bằng `ctypes` tại đường dẫn:

```text
dll/graph_core.dll
```

### Giải thích mã lỗi

Các hàm trong DLL trả về `0` nếu thành công. Nếu có lỗi, hàm trả về số âm.

| Mã lỗi | Ý nghĩa |
| --- | --- |
| `0` | Thành công |
| `-1` | Vượt quá giới hạn 5 đồ thị |
| `-2` | ID đồ thị không hợp lệ |
| `-3` | Loại hàm không hợp lệ |
| `-4` | Số lượng hệ số không hợp lệ |
| `-5` | Hệ số nằm ngoài khoảng `[-1000; 1000]` |
| `-7` | Buffer, con trỏ hoặc kích thước không hợp lệ |

Python có thể gọi hàm sau để lấy mã lỗi gần nhất:

```c
int get_error_code(void);
```

## 5. Hướng dẫn chạy

### Build DLL Assembly

Chạy các lệnh sau:

```bat
cd tới thư mục chứa build.bat
Ví dụ: cd /d D:\KTMT\Graphing\asm
build.bat
```

Nếu build thành công, màn hình sẽ hiển thị:

```text
Building graph_core.dll...
Done: ..\dll\graph_core.dll
```

File DLL sẽ được tạo tại:

```text
..\..\Graphing\dll\graph_core.dll
```

### Chạy chương trình

Sau khi build DLL, thì chạy file main.py.

Nếu chương trình mở giao diện `GRAPHING`, quá trình chạy thành công.

### Lưu ý

- Nếu `build.bat` báo không tìm thấy NASM, cần cài NASM và thêm vào `PATH`.
- Nếu `build.bat` báo không tìm thấy gcc, cần cài MinGW-w64 và thêm vào `PATH`.
- Nếu chưa có `dll/graph_core.dll`, giao diện vẫn mở nhưng sẽ báo cần build DLL trước.
