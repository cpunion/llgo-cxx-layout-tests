//go:build !llgo

package padding

import (
	"testing"
	"unsafe"
)

func TestOrdinaryGoLayout(t *testing.T) {
	if unsafe.Sizeof(Single{}) != 0 {
		t.Fatal("Go empty member must remain zero sized")
	}
	if unsafe.Offsetof(TwoSame{}.X) != 4 {
		t.Fatal("explicit byte precedes X")
	}
	if unsafe.Sizeof(EmptyArray{}) != 4 {
		t.Fatal("ordinary Go empty array has zero element stride")
	}
}
