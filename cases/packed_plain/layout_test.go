package probe

import (
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Packed{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct Packed) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Alignof(Packed{})), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __alignof__(struct Packed) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Packed{}.X)), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct Packed,x) Go=%d C=%d", got, want)
	}
}
