package probe

import _ "unsafe"

const LLGoFiles = "_native/oracle.c"

//go:linkname round C.round_union
func round(x FloatUnion) FloatUnion

//go:linkname nativeFact C.audit_fact
func nativeFact(i int32) uint64
