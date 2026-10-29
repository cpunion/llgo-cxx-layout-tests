package pr761

import (
	"testing"
	"unsafe"
)

func TestVirtualPrimary(t *testing.T) {
	for i, got := range []uintptr{unsafe.Sizeof(A{}), unsafe.Sizeof(Join{}), unsafe.Offsetof(A{}.V), unsafe.Offsetof(Join{}.Plain), unsafe.Offsetof(Join{}.Left), unsafe.Offsetof(Join{}.Shared)} {
		if want := nativeFact(int32(i)); uint64(got) != want {
			t.Errorf("AUDIT_VIRTUAL fact[%d] Go=%d C++=%d", i, got, want)
		}
	}
}
