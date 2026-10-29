package layout_runtime

import (
	"reflect"
	"testing"
	"unsafe"
)

//llgo:packed
type Packed[T any] struct {
	A byte
	X T
}

//llgo:pack 2
type Pack2[T any] struct {
	A byte
	X T
}
type Inner[T any] struct {
	A byte
	X T
}
type Outer[T any] struct {
	Prefix byte
	Inner[T]
}

//llgo:cdecl
type NativeFunc func()
type GoFunc func()

func packed[T any](v Packed[T]) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func pack2[T any](v Pack2[T]) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func outer[T any](v Outer[T]) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func size[T any](v T) uintptr { return unsafe.Sizeof(v) }
func TestStaticGenericAndActualLayout(t *testing.T) {
	p := Packed[int32]{}
	q := Pack2[int32]{}
	o := Outer[int32]{}
	cases := []struct {
		name      string
		got, want [3]uintptr
	}{
		{"packed", packed(p), [3]uintptr{unsafe.Sizeof(p), unsafe.Alignof(p), unsafe.Offsetof(p.X)}},
		{"pack2", pack2(q), [3]uintptr{unsafe.Sizeof(q), unsafe.Alignof(q), unsafe.Offsetof(q.X)}},
		{"promoted", outer(o), [3]uintptr{unsafe.Sizeof(o), unsafe.Alignof(o), unsafe.Offsetof(o.X)}},
	}
	for _, c := range cases {
		if c.got != c.want {
			t.Errorf("AUDIT_SSA_GENERIC %s generic=%v static=%v", c.name, c.got, c.want)
		}
	}
	if got, want := unsafe.Offsetof(o.X), uintptr(unsafe.Pointer(&o.X))-uintptr(unsafe.Pointer(&o)); got != want {
		t.Errorf("AUDIT_SSA_ACTUAL promoted static=%d actual=%d", got, want)
	}
	if got, want := reflect.TypeOf(p).Field(1).Offset, unsafe.Offsetof(p.X); got != want {
		t.Errorf("AUDIT_SSA_REFLECT packed offset=%d static=%d", got, want)
	}
	var native NativeFunc
	var gofn GoFunc
	if got, want := size(native), unsafe.Sizeof(native); got != want {
		t.Errorf("AUDIT_SSA_NATIVE generic=%d static=%d", got, want)
	}
	if got, want := size(gofn), unsafe.Sizeof(gofn); got != want {
		t.Errorf("AUDIT_SSA_FUNCVAL generic=%d static=%d", got, want)
	}
}
