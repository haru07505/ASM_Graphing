bits 64
default rel

section .text
global graphing_abi_version

; int graphing_abi_version(void)
graphing_abi_version:
    mov eax, 1
    ret
