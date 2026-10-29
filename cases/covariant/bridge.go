package probe

import _ "unsafe"

const LLGoFiles = "-std=c++20: _native/oracle.cpp"

//go:linkname create C.get_factory
func create() *FactoryDerived

//go:linkname expected C.get_result
func expected() *ReturnDerived
