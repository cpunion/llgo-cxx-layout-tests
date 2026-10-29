package probe

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Flags16{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct Flags16): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Alignof(Flags16{})), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __alignof__(struct Flags16): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Sizeof(Container{})), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct Container): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Container{}.Flags)), nativeFact(3); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct Container,flags): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Container{}.Suffix)), nativeFact(4); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct Container,suffix): Go=%d C=%d", got, want)
	}
	if got, want := uint64(reflect.TypeOf(Flags16{}).Size()), nativeFact(0); got != want {
		t.Errorf("AUDIT_REFLECT Flags16: Go=%d C=%d", got, want)
	}
}
