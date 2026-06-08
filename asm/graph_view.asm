bits 64
default rel

MAX_GRAPHS     equ 5
ERR_OK         equ 0
ERR_INVALID_ID equ -2
ERR_BUFFER     equ -7

extern graph_used
extern graph_visible
extern graph_type
extern graph_coeffs
extern last_error
extern eval_graph_y

section .data
base_scale dq 50.0
view_zoom dq 1.0
view_offset_x dq 0.0
view_offset_y dq 0.0
zoom_min dq 0.1
zoom_max dq 10.0
zoom_in_factor dq 1.1
zoom_out_factor dq 0.9
half dq 0.5
hundred dq 100.0
zero dq 0.0
one dq 1.0
two dq 2.0
five dq 5.0
ten dq 10.0
twelve dq 12.0
large dq 1.0e300

section .text
global generate_points
global generate_axis_ticks
global find_nearest_graph_point
global zoom_in
global zoom_out
global pan
global reset_view
global screen_to_math
global math_to_screen
global get_zoom_percent

; int generate_points(int id, int width, int height, double* out_xy, int max_pairs)
generate_points:
    mov r10d, [rsp + 40]

    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, 80

    mov ebx, ecx
    mov esi, edx
    mov edi, r8d
    mov r12, r9
    mov r15d, r10d

    cmp ebx, 0
    jl .invalid_id
    cmp ebx, MAX_GRAPHS
    jge .invalid_id
    test esi, esi
    jle .bad_buffer
    test edi, edi
    jle .bad_buffer
    test r12, r12
    jz .bad_buffer
    test r15d, r15d
    jle .bad_buffer

    lea r10, [graph_used]
    cmp dword [r10 + rbx * 4], 0
    je .invalid_id

    lea r10, [graph_visible]
    cmp dword [r10 + rbx * 4], 0
    je .return_zero

    lea r10, [graph_type]
    mov r13d, [r10 + rbx * 4]

    movsd xmm0, [base_scale]
    mulsd xmm0, [view_zoom]
    movsd [rsp + 32], xmm0

    cvtsi2sd xmm0, esi
    mulsd xmm0, [half]
    movsd [rsp + 40], xmm0

    cvtsi2sd xmm0, edi
    mulsd xmm0, [half]
    movsd [rsp + 48], xmm0

    xor r14d, r14d
.loop:
    cmp r14d, esi
    jge .points_done
    cmp r14d, r15d
    jge .points_done

    cvtsi2sd xmm0, r14d
    subsd xmm0, [rsp + 40]
    subsd xmm0, [view_offset_x]
    divsd xmm0, [rsp + 32]
    movsd [rsp + 56], xmm0

    mov ecx, r13d
    mov rax, rbx
    shl rax, 5
    lea rdx, [graph_coeffs]
    add rdx, rax
    movsd xmm2, [rsp + 56]
    lea r9, [rsp + 64]
    call eval_graph_y
    test eax, eax
    js .points_done

    mov rax, r14
    shl rax, 4
    cvtsi2sd xmm0, r14d
    movsd [r12 + rax], xmm0

    movsd xmm0, [rsp + 64]
    mulsd xmm0, [rsp + 32]
    movsd xmm1, [rsp + 48]
    addsd xmm1, [view_offset_y]
    subsd xmm1, xmm0
    movsd [r12 + rax + 8], xmm1

    inc r14d
    jmp .loop

.points_done:
    mov dword [last_error], ERR_OK
    mov eax, r14d
    jmp .done

.return_zero:
    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .done

.invalid_id:
    mov eax, ERR_INVALID_ID
    mov [last_error], eax
    jmp .done

.bad_buffer:
    mov eax, ERR_BUFFER
    mov [last_error], eax

.done:
    add rsp, 80
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    ret

; int generate_axis_ticks(int axis, int width, int height, double* out_pairs, int max_pairs)
; axis = 0: truc X, axis = 1: truc Y.
; out_pairs gom cac cap [screen_position, math_value].
generate_axis_ticks:
    mov r10d, [rsp + 40]

    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, 112

    mov ebx, ecx
    mov esi, edx
    mov edi, r8d
    mov r12, r9
    mov r15d, r10d

    cmp ebx, 0
    jl .axis_bad
    cmp ebx, 1
    jg .axis_bad
    test esi, esi
    jle .axis_bad
    test edi, edi
    jle .axis_bad
    test r12, r12
    jz .axis_bad
    test r15d, r15d
    jle .axis_bad

    movsd xmm0, [base_scale]
    mulsd xmm0, [view_zoom]
    movsd [rsp + 32], xmm0

    cvtsi2sd xmm0, esi
    mulsd xmm0, [half]
    movsd [rsp + 40], xmm0

    cvtsi2sd xmm0, edi
    mulsd xmm0, [half]
    movsd [rsp + 48], xmm0

    cmp ebx, 0
    je .axis_x_range

.axis_y_range:
    movsd xmm0, [rsp + 48]
    addsd xmm0, [view_offset_y]
    cvtsi2sd xmm1, edi
    subsd xmm0, xmm1
    divsd xmm0, [rsp + 32]
    movsd [rsp + 56], xmm0

    movsd xmm0, [rsp + 48]
    addsd xmm0, [view_offset_y]
    divsd xmm0, [rsp + 32]
    movsd [rsp + 64], xmm0
    jmp .axis_step

.axis_x_range:
    movsd xmm0, [zero]
    subsd xmm0, [rsp + 40]
    subsd xmm0, [view_offset_x]
    divsd xmm0, [rsp + 32]
    movsd [rsp + 56], xmm0

    cvtsi2sd xmm0, esi
    subsd xmm0, [rsp + 40]
    subsd xmm0, [view_offset_x]
    divsd xmm0, [rsp + 32]
    movsd [rsp + 64], xmm0

.axis_step:
    movsd xmm0, [rsp + 64]
    subsd xmm0, [rsp + 56]
    call nice_step
    movsd [rsp + 72], xmm0

    movsd xmm0, [rsp + 56]
    divsd xmm0, [rsp + 72]
    cvttsd2si rax, xmm0
    cvtsi2sd xmm1, rax
    mulsd xmm1, [rsp + 72]
    ucomisd xmm1, [rsp + 56]
    jbe .axis_have_start
    subsd xmm1, [rsp + 72]

.axis_have_start:
    movsd [rsp + 80], xmm1
    xor r14d, r14d

.axis_loop:
    cmp r14d, r15d
    jge .axis_done

    movsd xmm0, [rsp + 64]
    addsd xmm0, [rsp + 72]
    movsd xmm1, [rsp + 80]
    ucomisd xmm1, xmm0
    ja .axis_done

    cmp ebx, 0
    je .axis_store_x

.axis_store_y:
    movsd xmm0, [rsp + 80]
    mulsd xmm0, [rsp + 32]
    movsd xmm1, [rsp + 48]
    addsd xmm1, [view_offset_y]
    subsd xmm1, xmm0
    jmp .axis_store_pair

.axis_store_x:
    movsd xmm1, [rsp + 80]
    mulsd xmm1, [rsp + 32]
    addsd xmm1, [rsp + 40]
    addsd xmm1, [view_offset_x]

.axis_store_pair:
    mov rax, r14
    shl rax, 4
    movsd [r12 + rax], xmm1
    movsd xmm0, [rsp + 80]
    movsd [r12 + rax + 8], xmm0

    movsd xmm0, [rsp + 80]
    addsd xmm0, [rsp + 72]
    movsd [rsp + 80], xmm0
    inc r14d
    jmp .axis_loop

.axis_done:
    mov dword [last_error], ERR_OK
    mov eax, r14d
    jmp .axis_return

.axis_bad:
    mov eax, ERR_BUFFER
    mov [last_error], eax

.axis_return:
    add rsp, 112
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    ret

; int find_nearest_graph_point(double sx, double sy, int id, int width, int height, double* out_values)
; out_values = [screen_x, screen_y, math_x, math_y].
find_nearest_graph_point:
    mov r10d, [rsp + 40]
    mov r11, [rsp + 48]

    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, 144

    mov ebx, r8d
    mov esi, r9d
    mov edi, r10d
    mov r12, r11
    movsd [rsp + 56], xmm0
    movsd [rsp + 64], xmm1

    cmp ebx, 0
    jl .nearest_invalid_id
    cmp ebx, MAX_GRAPHS
    jge .nearest_invalid_id
    test esi, esi
    jle .nearest_bad
    test edi, edi
    jle .nearest_bad
    test r12, r12
    jz .nearest_bad

    lea r10, [graph_used]
    cmp dword [r10 + rbx * 4], 0
    je .nearest_invalid_id

    lea r10, [graph_visible]
    cmp dword [r10 + rbx * 4], 0
    je .nearest_not_found

    lea r10, [graph_type]
    mov r13d, [r10 + rbx * 4]

    movsd xmm0, [base_scale]
    mulsd xmm0, [view_zoom]
    movsd [rsp + 32], xmm0

    cvtsi2sd xmm0, esi
    mulsd xmm0, [half]
    movsd [rsp + 40], xmm0

    cvtsi2sd xmm0, edi
    mulsd xmm0, [half]
    movsd [rsp + 48], xmm0

    movsd xmm0, [large]
    movsd [rsp + 72], xmm0
    xor r14d, r14d

.nearest_loop:
    cmp r14d, esi
    jge .nearest_done

    cvtsi2sd xmm0, r14d
    subsd xmm0, [rsp + 40]
    subsd xmm0, [view_offset_x]
    divsd xmm0, [rsp + 32]
    movsd [rsp + 96], xmm0

    mov ecx, r13d
    mov rax, rbx
    shl rax, 5
    lea rdx, [graph_coeffs]
    add rdx, rax
    movsd xmm2, [rsp + 96]
    lea r9, [rsp + 112]
    call eval_graph_y
    test eax, eax
    js .nearest_eval_fail

    movsd xmm0, [rsp + 112]
    mulsd xmm0, [rsp + 32]
    movsd xmm1, [rsp + 48]
    addsd xmm1, [view_offset_y]
    subsd xmm1, xmm0
    movsd [rsp + 104], xmm1

    cvtsi2sd xmm0, r14d
    subsd xmm0, [rsp + 56]
    mulsd xmm0, xmm0
    movsd xmm1, [rsp + 104]
    subsd xmm1, [rsp + 64]
    mulsd xmm1, xmm1
    addsd xmm0, xmm1

    ucomisd xmm0, [rsp + 72]
    jae .nearest_next

    movsd [rsp + 72], xmm0
    cvtsi2sd xmm1, r14d
    movsd [rsp + 80], xmm1
    movsd xmm1, [rsp + 104]
    movsd [rsp + 88], xmm1
    movsd xmm1, [rsp + 96]
    movsd [rsp + 120], xmm1
    movsd xmm1, [rsp + 112]
    movsd [rsp + 128], xmm1

.nearest_next:
    inc r14d
    jmp .nearest_loop

.nearest_done:
    movsd xmm0, [rsp + 80]
    movsd [r12], xmm0
    movsd xmm0, [rsp + 88]
    movsd [r12 + 8], xmm0
    movsd xmm0, [rsp + 120]
    movsd [r12 + 16], xmm0
    movsd xmm0, [rsp + 128]
    movsd [r12 + 24], xmm0
    mov dword [last_error], ERR_OK
    mov eax, 1
    jmp .nearest_return

.nearest_not_found:
    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .nearest_return

.nearest_eval_fail:
    mov [last_error], eax
    jmp .nearest_return

.nearest_invalid_id:
    mov eax, ERR_INVALID_ID
    mov [last_error], eax
    jmp .nearest_return

.nearest_bad:
    mov eax, ERR_BUFFER
    mov [last_error], eax

.nearest_return:
    add rsp, 144
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    ret

; int zoom_in(void)
zoom_in:
    movsd xmm0, [view_zoom]
    mulsd xmm0, [zoom_in_factor]
    minsd xmm0, [zoom_max]
    movsd [view_zoom], xmm0
    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

; int zoom_out(void)
zoom_out:
    movsd xmm0, [view_zoom]
    mulsd xmm0, [zoom_out_factor]
    maxsd xmm0, [zoom_min]
    movsd [view_zoom], xmm0
    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

; int pan(double dx, double dy)
pan:
    addsd xmm0, [view_offset_x]
    movsd [view_offset_x], xmm0
    addsd xmm1, [view_offset_y]
    movsd [view_offset_y], xmm1
    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

; int reset_view(void)
reset_view:
    movsd xmm0, [zero]
    movsd [view_offset_x], xmm0
    movsd [view_offset_y], xmm0
    movsd xmm0, [one]
    movsd [view_zoom], xmm0
    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

; int screen_to_math(double sx, double sy, int width, int height, double* out_x, double* out_y)
screen_to_math:
    mov r10, [rsp + 40]
    mov r11, [rsp + 48]
    test r10, r10
    jz .screen_bad
    test r11, r11
    jz .screen_bad

    movsd xmm2, [base_scale]
    mulsd xmm2, [view_zoom]

    cvtsi2sd xmm3, r8d
    mulsd xmm3, [half]
    subsd xmm0, xmm3
    subsd xmm0, [view_offset_x]
    divsd xmm0, xmm2
    movsd [r10], xmm0

    cvtsi2sd xmm4, r9d
    mulsd xmm4, [half]
    addsd xmm4, [view_offset_y]
    subsd xmm4, xmm1
    divsd xmm4, xmm2
    movsd [r11], xmm4

    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

.screen_bad:
    mov eax, ERR_BUFFER
    mov [last_error], eax
    ret

; int math_to_screen(double x, double y, int width, int height, double* out_x, double* out_y)
math_to_screen:
    mov r10, [rsp + 40]
    mov r11, [rsp + 48]
    test r10, r10
    jz .math_bad
    test r11, r11
    jz .math_bad

    movsd xmm2, [base_scale]
    mulsd xmm2, [view_zoom]

    mulsd xmm0, xmm2
    cvtsi2sd xmm3, r8d
    mulsd xmm3, [half]
    addsd xmm0, xmm3
    addsd xmm0, [view_offset_x]
    movsd [r10], xmm0

    mulsd xmm1, xmm2
    cvtsi2sd xmm4, r9d
    mulsd xmm4, [half]
    addsd xmm4, [view_offset_y]
    subsd xmm4, xmm1
    movsd [r11], xmm4

    mov dword [last_error], ERR_OK
    xor eax, eax
    ret

.math_bad:
    mov eax, ERR_BUFFER
    mov [last_error], eax
    ret

; double get_zoom_percent(void)
get_zoom_percent:
    movsd xmm0, [view_zoom]
    mulsd xmm0, [hundred]
    ret

; double nice_step(double span)
; Tra ve buoc chia dep theo dang 1, 2, 5 nhan voi luy thua cua 10.
nice_step:
    divsd xmm0, [twelve]
    ucomisd xmm0, [zero]
    jbe .nice_one

    movsd xmm1, [one]

.nice_scale_down:
    ucomisd xmm0, [ten]
    jb .nice_scale_up
    divsd xmm0, [ten]
    mulsd xmm1, [ten]
    jmp .nice_scale_down

.nice_scale_up:
    ucomisd xmm0, [one]
    jae .nice_choose
    mulsd xmm0, [ten]
    divsd xmm1, [ten]
    jmp .nice_scale_up

.nice_choose:
    ucomisd xmm0, [two]
    jb .nice_magnitude
    ucomisd xmm0, [five]
    jb .nice_two
    movsd xmm0, xmm1
    mulsd xmm0, [five]
    ret

.nice_two:
    movsd xmm0, xmm1
    mulsd xmm0, [two]
    ret

.nice_magnitude:
    movsd xmm0, xmm1
    ret

.nice_one:
    movsd xmm0, [one]
    ret
