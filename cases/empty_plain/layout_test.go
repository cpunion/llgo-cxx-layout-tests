package probe

import (
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Single{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(Single) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Sizeof(EmptyArray{})), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(EmptyArray) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(EmptyArray{}.X)), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(EmptyArray,x) Go=%d C=%d", got, want)
	}
}
