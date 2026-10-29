package probe

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestNativeLayout(t *testing.T) {
	if got, want := uint64(unsafe.Sizeof(CallbackBits{})), nativeFact(0); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(struct CallbackBits): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Offsetof(CallbackBits{}.Callback)), nativeFact(1); got != want {
		t.Errorf("AUDIT_LAYOUT __builtin_offsetof(struct CallbackBits,callback): Go=%d C=%d", got, want)
	}
	if got, want := uint64(unsafe.Sizeof(CallbackBits{}.Callback)), nativeFact(2); got != want {
		t.Errorf("AUDIT_LAYOUT sizeof(((struct CallbackBits*)0)->callback): Go=%d C=%d", got, want)
	}
	if got, want := uint64(reflect.TypeOf(CallbackBits{}).Size()), nativeFact(0); got != want {
		t.Errorf("AUDIT_REFLECT CallbackBits: Go=%d C=%d", got, want)
	}
}
