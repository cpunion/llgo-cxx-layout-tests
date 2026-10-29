package probe

import _ "unsafe"

const LLGoFiles = "-std=c++20: _native/oracle.cpp"

//go:linkname nativeFact C.audit_fact
func nativeFact(i int32) uint64
