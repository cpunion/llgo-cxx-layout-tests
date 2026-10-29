ENTRY(_start)
MEMORY { FLASH (rx) : ORIGIN = 0, LENGTH = 4M
RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 4M }
SECTIONS {
 .vectors : { KEEP(*(.vectors)) } > FLASH
 .text : { *(.text*) *(.rodata*) } > FLASH
 .ARM.exidx : { *(.ARM.exidx*) } > FLASH
 .data : { *(.data*) } > RAM
 .bss : { *(.bss*) *(COMMON) } > RAM
}
