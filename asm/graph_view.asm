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

section .text
global generate_points
global zoom_in
global zoom_out
global pan
global reset_view
global screen_to_math
global math_to_screen
global get_zoom_percent

; int generate_points(int id, int width, int height, double* out_xy, int max_pairs)
generate_points:
    mov r15d, [rsp + 40]

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
