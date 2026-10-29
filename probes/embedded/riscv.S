.section .text.start,"ax"
.global _start
_start:
 la sp, _stack_top
 call audit_start
1: j 1b
