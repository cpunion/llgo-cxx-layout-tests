package pr761

import _ "unsafe"

const LLGoFiles = "$AUDIT_CXXFLAGS: _native/oracle.cpp"

//go:linkname nativeFact C.virtual_fact
func nativeFact(i int32) uint64
