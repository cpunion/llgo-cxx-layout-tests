package probe

import (
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Derived{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(Derived) Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Derived{}.D)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(Derived,d) Go=%d C=%d", got, want)
	}
}
