package probe

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Flexible{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct Flexible): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Flexible{}.Data)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct Flexible,data): Go=%d C=%d", got, want)
	}
	if got, want := uint64(reflect.TypeOf(Flexible{}).Size()), nativeFact(0); got != want {
		t.Errorf("AUDIT_REFLECT Flexible: Go=%d C=%d", got, want)
	}
}
