bits 64
default rel

ERR_OK                 equ 0
ERR_INVALID_TYPE       equ -3
ERR_INVALID_COEFFCOUNT equ -4
ERR_COEFF_RANGE        equ -5

TYPE_LINEAR    equ 0
TYPE_QUADRATIC equ 1
TYPE_SIN       equ 2
TYPE_COS       equ 3

section .data
min_coeff dq -1000.0
max_coeff dq 1000.0

section .text
global validate_coefficients
global eval_graph_y

; int validate_coefficients(int type, double* coeffs, int coeff_count)
; Kiem tra khung: loai ham, so he so, mien [-1000; 1000].
; TODO: Neu can bat dung "toi da 4 chu so thap phan", nen truyen chuoi goc
;       hoac them API rieng, vi double da mat thong tin dinh dang ban dau.
validate_coefficients:
    cmp ecx, TYPE_LINEAR
    jl .invalid_type
    cmp ecx, TYPE_COS
    jg .invalid_type
    test rdx, rdx
    jz .invalid_count

    mov eax, 4
    cmp ecx, TYPE_SIN
    jge .have_expected
    mov eax, 3
    cmp ecx, TYPE_QUADRATIC
    je .have_expected
    mov eax, 2

.have_expected:
    cmp r8d, eax
    jl .invalid_count

    xor r9d, r9d
.range_loop:
    cmp r9d, eax
    jge .ok
    movsd xmm0, [rdx + r9 * 8]
    ucomisd xmm0, [min_coeff]
    jp .range_fail
    jb .range_fail
    ucomisd xmm0, [max_coeff]
    ja .range_fail
    inc r9d
    jmp .range_loop

.ok:
    mov eax, ERR_OK
    ret

.invalid_type:
    mov eax, ERR_INVALID_TYPE
    ret

.invalid_count:
    mov eax, ERR_INVALID_COEFFCOUNT
    ret

.range_fail:
    mov eax, ERR_COEFF_RANGE
    ret

; int eval_graph_y(int type, double* coeffs, double x, double* out_y)
; coeffs gom 4 double lien tiep: a, b, c, d.
eval_graph_y:
    test rdx, rdx
    jz .eval_invalid
    test r9, r9
    jz .eval_invalid

    cmp ecx, TYPE_LINEAR
    je .linear
    cmp ecx, TYPE_QUADRATIC
    je .quadratic
    cmp ecx, TYPE_SIN
    je .sin
    cmp ecx, TYPE_COS
    je .cos
    jmp .eval_invalid

.linear:
    movsd xmm0, [rdx]
    mulsd xmm0, xmm2
    addsd xmm0, [rdx + 8]
    movsd [r9], xmm0
    xor eax, eax
    ret

.quadratic:
    movapd xmm0, xmm2
    mulsd xmm0, xmm2
    mulsd xmm0, [rdx]

    movapd xmm1, xmm2
    mulsd xmm1, [rdx + 8]
    addsd xmm0, xmm1
    addsd xmm0, [rdx + 16]
    movsd [r9], xmm0
    xor eax, eax
    ret

.sin:
    sub rsp, 16
    movapd xmm0, xmm2
    mulsd xmm0, [rdx + 8]
    addsd xmm0, [rdx + 16]
    movsd [rsp], xmm0
    fld qword [rsp]
    fsin
    fstp qword [rsp]
    movsd xmm0, [rsp]
    add rsp, 16
    mulsd xmm0, [rdx]
    addsd xmm0, [rdx + 24]
    movsd [r9], xmm0
    xor eax, eax
    ret

.cos:
    sub rsp, 16
    movapd xmm0, xmm2
    mulsd xmm0, [rdx + 8]
    addsd xmm0, [rdx + 16]
    movsd [rsp], xmm0
    fld qword [rsp]
    fcos
    fstp qword [rsp]
    movsd xmm0, [rsp]
    add rsp, 16
    mulsd xmm0, [rdx]
    addsd xmm0, [rdx + 24]
    movsd [r9], xmm0
    xor eax, eax
    ret

.eval_invalid:
    mov eax, ERR_INVALID_TYPE
    ret
