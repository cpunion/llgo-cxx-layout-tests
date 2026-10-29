package probe

import (
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(TwoSame{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(TwoSame) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(TwoSame{}.B)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(TwoSame,b) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(TwoSame{}.X)), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(TwoSame,x) Go=%d C=%d", got, want)
	}
}
