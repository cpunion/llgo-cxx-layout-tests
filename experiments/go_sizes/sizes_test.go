// Package gosizes checks Go storage, not the size of referenced heap objects.
package gosizes

import (
	"reflect"
	"runtime"
	"testing"
	"unsafe"
)

type namedInt int
type namedString string
type namedFunc func(int) int
type aliasInt = namedInt
type aliasSlice[T any] = []T
type record[T any] struct {
	B byte
	V T
}
type empty struct{}
type tailEmpty struct {
	B byte
	Z empty
}
type headEmpty struct {
	Z empty
	B byte
}
type alignedEmpty struct {
	B byte
	Z [0]uint64
}
type recursive struct {
	Next  *recursive
	Value int
}
type recursiveSlice []recursiveSlice
type embedded struct {
	record[int32]
	Tail byte
}
type pointerEmbedded struct {
	*record[int32]
	Tail byte
}
type methodInterface interface{ M() }
type namedArray [3]uint16
type namedMap map[string]int
type namedChan chan int

// The expected data model is selected independently of unsafe.Sizeof.
func wordSize(t *testing.T) uintptr {
	t.Helper()
	switch runtime.GOARCH {
	case "386", "arm", "mips", "mipsle":
		return 4
	case "amd64", "arm64", "riscv64", "ppc64", "ppc64le", "mips64", "mips64le", "s390x", "loong64", "wasm":
		return 8
	default:
		t.Fatalf("unreviewed Go data model: %s/%s", runtime.GOOS, runtime.GOARCH)
		return 0
	}
}

// No T value crosses a call boundary: storage failures remain distinguishable
// from aggregate argument ABI failures. Each call supplies a concrete constant
// Sizeof expression, while this body separately exercises generic lowering.
func check[T any](t *testing.T, name string, constant, want uintptr) {
	t.Helper()
	t.Run(name, func(t *testing.T) {
		var v T
		var a [2]T
		rt := reflect.TypeOf((*T)(nil)).Elem()
		checks := []struct {
			name      string
			got, want uintptr
		}{
			{"constant", constant, want},
			{"generic", unsafe.Sizeof(v), want},
			{"array", unsafe.Sizeof(a), 2 * want},
			{"stride", uintptr(unsafe.Pointer(&a[1])) - uintptr(unsafe.Pointer(&a[0])), want},
			{"reflect", rt.Size(), want},
		}
		for _, c := range checks {
			if c.got != c.want {
				t.Errorf("%s size = %d, want %d", c.name, c.got, c.want)
			}
		}
	})
}

func TestGoTypeSizes(t *testing.T) {
	w := wordSize(t)
	a64 := w
	f := functionWords * w
	t.Logf("compiler=%s target=%s/%s GoWord=%d func=%d", runtime.Compiler, runtime.GOOS, runtime.GOARCH, w, f)
	check[bool](t, "bool", unsafe.Sizeof(false), 1)
	check[int8](t, "int8", unsafe.Sizeof(int8(0)), 1)
	check[uint8](t, "uint8", unsafe.Sizeof(uint8(0)), 1)
	check[byte](t, "byte", unsafe.Sizeof(byte(0)), 1)
	check[int16](t, "int16", unsafe.Sizeof(int16(0)), 2)
	check[uint16](t, "uint16", unsafe.Sizeof(uint16(0)), 2)
	check[int32](t, "int32", unsafe.Sizeof(int32(0)), 4)
	check[uint32](t, "uint32", unsafe.Sizeof(uint32(0)), 4)
	check[rune](t, "rune", unsafe.Sizeof(rune(0)), 4)
	check[int64](t, "int64", unsafe.Sizeof(int64(0)), 8)
	check[uint64](t, "uint64", unsafe.Sizeof(uint64(0)), 8)
	check[int](t, "int", unsafe.Sizeof(int(0)), w)
	check[uint](t, "uint", unsafe.Sizeof(uint(0)), w)
	check[uintptr](t, "uintptr", unsafe.Sizeof(uintptr(0)), w)
	check[float32](t, "float32", unsafe.Sizeof(float32(0)), 4)
	check[float64](t, "float64", unsafe.Sizeof(float64(0)), 8)
	check[complex64](t, "complex64", unsafe.Sizeof(complex64(0)), 8)
	check[complex128](t, "complex128", unsafe.Sizeof(complex128(0)), 16)
	check[unsafe.Pointer](t, "unsafe_pointer", unsafe.Sizeof(unsafe.Pointer(nil)), w)
	check[*byte](t, "pointer", unsafe.Sizeof((*byte)(nil)), w)
	check[**empty](t, "pointer_to_pointer", unsafe.Sizeof((**empty)(nil)), w)
	check[string](t, "string", unsafe.Sizeof(""), 2*w)
	check[[]int](t, "slice", unsafe.Sizeof([]int(nil)), 3*w)
	check[[]empty](t, "slice_empty_element", unsafe.Sizeof([]empty(nil)), 3*w)
	check[map[string]int](t, "map", unsafe.Sizeof(map[string]int(nil)), w)
	check[chan int](t, "chan", unsafe.Sizeof(chan int(nil)), w)
	check[<-chan int](t, "recv_chan", unsafe.Sizeof((<-chan int)(nil)), w)
	check[chan<- int](t, "send_chan", unsafe.Sizeof((chan<- int)(nil)), w)
	check[any](t, "empty_interface", unsafe.Sizeof(any(nil)), 2*w)
	check[methodInterface](t, "method_interface", unsafe.Sizeof(methodInterface(nil)), 2*w)
	check[func()](t, "func", unsafe.Sizeof((func())(nil)), f)
	check[func(...int) (int, error)](t, "variadic_func", unsafe.Sizeof((func(...int) (int, error))(nil)), f)
	check[[0]byte](t, "zero_array", unsafe.Sizeof([0]byte{}), 0)
	check[[0]uint64](t, "aligned_zero_array", unsafe.Sizeof([0]uint64{}), 0)
	check[[3]uint16](t, "array", unsafe.Sizeof([3]uint16{}), 6)
	check[[2][3]int](t, "nested_array", unsafe.Sizeof([2][3]int{}), 6*w)
	check[[2]*byte](t, "pointer_array", unsafe.Sizeof([2]*byte{}), 2*w)
	check[[3]func()](t, "func_array", unsafe.Sizeof([3]func(){}), 3*f)
	check[[3]empty](t, "empty_array", unsafe.Sizeof([3]empty{}), 0)
	check[empty](t, "empty_struct", unsafe.Sizeof(empty{}), 0)
	check[tailEmpty](t, "zero_tail_struct", unsafe.Sizeof(tailEmpty{}), 2)
	check[headEmpty](t, "zero_head_struct", unsafe.Sizeof(headEmpty{}), 1)
	check[alignedEmpty](t, "aligned_zero_tail_struct", unsafe.Sizeof(alignedEmpty{}), 2*a64)
	check[record[int32]](t, "generic_struct_int32", unsafe.Sizeof(record[int32]{}), 8)
	check[record[uint64]](t, "generic_struct_uint64", unsafe.Sizeof(record[uint64]{}), a64+8)
	check[record[float64]](t, "generic_struct_float64", unsafe.Sizeof(record[float64]{}), a64+8)
	check[record[func()]](t, "generic_struct_func", unsafe.Sizeof(record[func()]{}), w+f)
	check[record[empty]](t, "generic_struct_empty", unsafe.Sizeof(record[empty]{}), 2)
	check[embedded](t, "embedded_struct", unsafe.Sizeof(embedded{}), 12)
	check[pointerEmbedded](t, "embedded_pointer_struct", unsafe.Sizeof(pointerEmbedded{}), 2*w)
	check[recursive](t, "recursive_struct", unsafe.Sizeof(recursive{}), 2*w)
	check[recursiveSlice](t, "recursive_slice", unsafe.Sizeof(recursiveSlice(nil)), 3*w)
	check[namedInt](t, "named_int", unsafe.Sizeof(namedInt(0)), w)
	check[aliasInt](t, "alias_named_int", unsafe.Sizeof(aliasInt(0)), w)
	check[namedString](t, "named_string", unsafe.Sizeof(namedString("")), 2*w)
	check[namedFunc](t, "named_func", unsafe.Sizeof(namedFunc(nil)), f)
	check[namedArray](t, "named_array", unsafe.Sizeof(namedArray{}), 6)
	check[namedMap](t, "named_map", unsafe.Sizeof(namedMap(nil)), w)
	check[namedChan](t, "named_chan", unsafe.Sizeof(namedChan(nil)), w)
	check[aliasSlice[int]](t, "generic_alias", unsafe.Sizeof(aliasSlice[int](nil)), 3*w)
	check[struct {
		A byte
		B byte
	}](t, "anonymous_struct", unsafe.Sizeof(struct {
		A byte
		B byte
	}{}), 2)
	check[struct {
		_ uint64
		B byte
	}](t, "blank_field_struct", unsafe.Sizeof(struct {
		_ uint64
		B byte
	}{}), 8+a64)
}
