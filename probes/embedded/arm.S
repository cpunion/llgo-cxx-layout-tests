.syntax unified
.cpu cortex-m3
.thumb
.section .vectors,"a"
.word 0x20010000
.word _start
.text
.global _start
.thumb_func
_start:
 bl audit_start
 b .
