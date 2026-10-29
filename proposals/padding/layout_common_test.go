package padding

import (
	"reflect"
	"testing"
	"unsafe"
)

func TestInterfaceAndReflection(t *testing.T) {
	cases := []struct {
		value any
		size  uintptr
	}{
		{Bar2{}, unsafe.Sizeof(Bar2{})}, {TwoSame{}, unsafe.Sizeof(TwoSame{})},
		{Mixed{}, unsafe.Sizeof(Mixed{})}, {Single{}, unsafe.Sizeof(Single{})},
		{Nested[Inner, Empty]{}, unsafe.Sizeof(Nested[Inner, Empty]{})},
		{Reuse[Tail]{}, unsafe.Sizeof(Reuse[Tail]{})},
		{Pair[Empty, Empty2]{}, unsafe.Sizeof(Pair[Empty, Empty2]{})},
		{EmptyArray{}, unsafe.Sizeof(EmptyArray{})},
	}
	for _, c := range cases {
		if got := reflect.TypeOf(c.value).Size(); got != c.size {
			t.Errorf("%T reflection=%d unsafe=%d", c.value, got, c.size)
		}
	}
}
