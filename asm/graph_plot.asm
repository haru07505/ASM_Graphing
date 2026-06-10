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

extern base_scale
extern view_zoom
extern view_offset_x
extern view_offset_y
extern half

section .text
global generate_points

; int generate_points(int id, int width, int height, double* out_xy, int max_pairs)
; Sinh cac cap toa do man hinh [x0, y0, x1, y1, ...] de Python Canvas ve.
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
