package probe

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Derived{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(Derived): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Derived{}.Tail)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(Derived,tail): Go=%d C=%d", got, want)
	}
	if got, want := uint64(reflect.TypeOf(Derived{}).Size()), nativeFact(0); got != want {
		t.Errorf("AUDIT_REFLECT Derived: Go=%d C=%d", got, want)
	}
}
