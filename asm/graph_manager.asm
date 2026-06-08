bits 64
default rel

MAX_GRAPHS             equ 5
ERR_OK                 equ 0
ERR_FULL               equ -1
ERR_INVALID_ID         equ -2

extern validate_coefficients

section .data
global graph_used
global graph_visible
global graph_type
global graph_color
global graph_coeffs
global graph_count
global last_error

graph_used    dd 0, 0, 0, 0, 0
graph_visible dd 0, 0, 0, 0, 0
graph_type    dd 0, 0, 0, 0, 0
graph_color   dd 0, 0, 0, 0, 0
graph_coeffs  times 20 dq 0.0
graph_count   dd 0
last_error    dd 0

section .text
global get_error_code
global get_graph_count
global add_graph
global edit_graph
global delete_graph
global set_visible
global set_color

get_error_code:
    mov eax, [last_error]
    ret

get_graph_count:
    mov eax, [graph_count]
    ret

; int add_graph(int type, double* coeffs, int coeff_count, int color_rgb)
add_graph:
    push rbx
    push rsi
    push rdi
    sub rsp, 32

    mov ebx, ecx
    mov rsi, rdx
    mov edi, r9d

    call validate_coefficients
    test eax, eax
    js .add_fail

    cmp dword [graph_count], MAX_GRAPHS
    jge .add_full

    xor eax, eax
    lea r10, [graph_used]
.find_slot:
    cmp eax, MAX_GRAPHS
    jge .add_full
    cmp dword [r10 + rax * 4], 0
    je .store_slot
    inc eax
    jmp .find_slot

.store_slot:
    mov dword [r10 + rax * 4], 1
    lea r11, [graph_visible]
    mov dword [r11 + rax * 4], 1
    lea r11, [graph_type]
    mov dword [r11 + rax * 4], ebx
    lea r11, [graph_color]
    mov dword [r11 + rax * 4], edi

    mov r8, rax
    shl r8, 5
    lea r11, [graph_coeffs]
    add r11, r8
    movsd xmm0, [rsi]
    movsd [r11], xmm0
    movsd xmm0, [rsi + 8]
    movsd [r11 + 8], xmm0
    movsd xmm0, [rsi + 16]
    movsd [r11 + 16], xmm0
    movsd xmm0, [rsi + 24]
    movsd [r11 + 24], xmm0

    inc dword [graph_count]
    mov dword [last_error], ERR_OK
    jmp .add_done

.add_full:
    mov eax, ERR_FULL

.add_fail:
    mov [last_error], eax

.add_done:
    add rsp, 32
    pop rdi
    pop rsi
    pop rbx
    ret

; int edit_graph(int id, int type, double* coeffs, int coeff_count)
edit_graph:
    push rbx
    push rsi
    push rdi
    push r12
    sub rsp, 40

    mov ebx, ecx
    mov edi, edx
    mov rsi, r8
    mov r12d, r9d

    call validate_id
    test eax, eax
    js .edit_fail

    mov ecx, edi
    mov rdx, rsi
    mov r8d, r12d
    call validate_coefficients
    test eax, eax
    js .edit_fail

    lea r10, [graph_type]
    mov dword [r10 + rbx * 4], edi

    mov r11, rbx
    shl r11, 5
    lea r10, [graph_coeffs]
    add r10, r11
    movsd xmm0, [rsi]
    movsd [r10], xmm0
    movsd xmm0, [rsi + 8]
    movsd [r10 + 8], xmm0
    movsd xmm0, [rsi + 16]
    movsd [r10 + 16], xmm0
    movsd xmm0, [rsi + 24]
    movsd [r10 + 24], xmm0

    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .edit_done

.edit_fail:
    mov [last_error], eax

.edit_done:
    add rsp, 40
    pop r12
    pop rdi
    pop rsi
    pop rbx
    ret

; int delete_graph(int id)
delete_graph:
    push rbx
    sub rsp, 32
    mov ebx, ecx

    call validate_id
    test eax, eax
    js .delete_fail

    lea r10, [graph_used]
    mov dword [r10 + rbx * 4], 0
    lea r10, [graph_visible]
    mov dword [r10 + rbx * 4], 0
    dec dword [graph_count]
    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .delete_done

.delete_fail:
    mov [last_error], eax

.delete_done:
    add rsp, 32
    pop rbx
    ret

; int set_visible(int id, int visible)
set_visible:
    push rbx
    push rdi
    sub rsp, 40
    mov ebx, ecx
    mov edi, edx

    call validate_id
    test eax, eax
    js .visible_fail

    xor eax, eax
    test edi, edi
    setnz al
    lea r10, [graph_visible]
    mov [r10 + rbx * 4], eax
    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .visible_done

.visible_fail:
    mov [last_error], eax

.visible_done:
    add rsp, 40
    pop rdi
    pop rbx
    ret

; int set_color(int id, int color_rgb)
set_color:
    push rbx
    push rdi
    sub rsp, 40
    mov ebx, ecx
    mov edi, edx

    call validate_id
    test eax, eax
    js .color_fail

    lea r10, [graph_color]
    mov [r10 + rbx * 4], edi
    mov dword [last_error], ERR_OK
    xor eax, eax
    jmp .color_done

.color_fail:
    mov [last_error], eax

.color_done:
    add rsp, 40
    pop rdi
    pop rbx
    ret

; int validate_id(int id)
validate_id:
    cmp ebx, 0
    jl .invalid
    cmp ebx, MAX_GRAPHS
    jge .invalid
    lea r10, [graph_used]
    cmp dword [r10 + rbx * 4], 0
    je .invalid
    xor eax, eax
    ret

.invalid:
    mov eax, ERR_INVALID_ID
    ret
