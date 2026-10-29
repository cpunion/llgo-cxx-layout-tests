package probe

import _ "unsafe"

const LLGoFiles = "_native/oracle.c"

//go:linkname nativeFact C.audit_fact
func nativeFact(i int32) uint64
