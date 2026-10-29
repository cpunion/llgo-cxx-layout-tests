//go:build llgo

package padding

import _ "unsafe"

const LLGoFiles = "$AUDIT_CXXFLAGS: _native/oracle.cpp"

//go:linkname nativeFact C.padding_fact
func nativeFact(index int32) uint64
