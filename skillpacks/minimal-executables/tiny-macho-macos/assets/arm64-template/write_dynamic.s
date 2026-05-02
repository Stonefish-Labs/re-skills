.globl _start
.p2align 2
_start:
    mov x0, #1
    adr x1, msg
    mov x2, #3
    mov x16, #4
    svc #0x80
    mov x0, #0
    mov x16, #1
    svc #0x80
msg:
    .ascii "hi\n"
