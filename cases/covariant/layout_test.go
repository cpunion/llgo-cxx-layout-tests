package probe

import (
	"testing"
	"unsafe"
)

func TestCovariant(t *testing.T) {
	f := create()
	got := f.XGo_vptr().Make(f)
	want := expected()
	if got != want {
		t.Errorf("AUDIT_COVARIANT pointer delta=%d want=0", int64(uintptr(unsafe.Pointer(got))-uintptr(unsafe.Pointer(want))))
	}
}
