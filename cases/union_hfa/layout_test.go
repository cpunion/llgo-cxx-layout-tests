package probe

import (
	"testing"
	"unsafe"
)

func TestUnionABI(t *testing.T) {
	var x FloatUnion
	if got, want := uint64(unsafe.Sizeof(x)), nativeFact(0); got != want {
		t.Fatalf("AUDIT_LAYOUT size Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Alignof(x)), nativeFact(1); got != want {
		t.Fatalf("AUDIT_LAYOUT align Go=%d C=%d", got, want)
	}
	x.XGof_ref_a().X = 3
	x.XGof_ref_a().Y = 5
	y := round(x)
	if y.XGof_ref_a().X != 4 || y.XGof_ref_a().Y != 7 {
		t.Errorf("AUDIT_HFA got=(%v,%v) want=(4,7)", y.XGof_ref_a().X, y.XGof_ref_a().Y)
	}
}
