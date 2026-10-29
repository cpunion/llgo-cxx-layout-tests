//go:build llgo

package layout_runtime

import (
	"testing"
	"unsafe"
)

func TestPackedValues(t *testing.T) {
	if got := packed(Packed[int32]{}); got != [3]uintptr{5, 1, 1} {
		t.Errorf("AUDIT_PACKED_VALUES %v", got)
	}
	if got := pack2(Pack2[int32]{}); got != [3]uintptr{6, 2, 2} {
		t.Errorf("AUDIT_PACKED_VALUES %v", got)
	}
	var n NativeFunc
	var g GoFunc
	if unsafe.Sizeof(n) != unsafe.Sizeof(uintptr(0)) || unsafe.Sizeof(g) != 2*unsafe.Sizeof(uintptr(0)) {
		t.Fatal("AUDIT_CALLBACK_VALUES native or closure size")
	}
}
