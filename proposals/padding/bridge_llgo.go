//go:build llgo

package padding

import _ "unsafe"

const LLGoFiles = "-std=c++20: _native/oracle.cpp"

//go:linkname nativeFact C.padding_fact
func nativeFact(index int32) uint64
