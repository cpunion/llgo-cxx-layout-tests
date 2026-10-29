// Generated with llcppg PR #761 at fcfde2b6b240bfe8e470d363b412cbe79b7adf78, Clang 22.1.8, macOS arm64.
package pr761

import (
	"github.com/goplus/lib/c"
	"unsafe"
)

type V struct {
	_xgo_vptr unsafe.Pointer
}
type A struct {
	_xgo_vptr unsafe.Pointer
	A         c.Int
	V
}
type Plain struct {
	P c.Int
}
type Shared struct {
	Shared c.Int
}
type Left struct {
	_xgo_vptr unsafe.Pointer
	Left      c.Int
	Shared
}
type Join struct {
	Plain
	_xgo_vptr unsafe.Pointer
	Left      c.Int
	Shared
}

// llgo:type C
type _xgo_vtable_V struct {
	Value func(this *V) c.Int
}

func (p *V) XGo_vptr() *_xgo_vtable_V {
	return (*_xgo_vtable_V)(p._xgo_vptr)
}

// llgo:link (*V).Value C._ZN1V5valueEv
func (this *V) Value() c.Int {
	return 0
}
