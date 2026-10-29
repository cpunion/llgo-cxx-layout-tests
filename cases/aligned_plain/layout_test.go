package probe

import (
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Aligned{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(Aligned) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Alignof(Aligned{})), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT alignof(Aligned) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Sizeof(AlignedBox{})), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(AlignedBox) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(AlignedBox{}.Value)), nativeFact(3); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(AlignedBox,value) Go=%d C=%d", got, want)
	}
}
