package probe

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(Packet{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct Packet): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(Packet{}.Payload)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct Packet,payload): Go=%d C=%d", got, want)
	}
	if got, want := uint64(reflect.TypeOf(Packet{}).Size()), nativeFact(0); got != want {
		t.Errorf("AUDIT_REFLECT Packet: Go=%d C=%d", got, want)
	}
}
