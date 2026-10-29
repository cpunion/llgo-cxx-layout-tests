//go:build llgo

package padding

import (
	"testing"
	"unsafe"
)

func TestNativeCppCompatibility(t *testing.T) {
	t.Run("Bar2.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Bar2{})), nativeFact(2); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Bar2.f", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Bar2{}.F)), nativeFact(4); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Bar2.field_size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Bar2{}.F)), nativeFact(5); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("TwoSame.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(TwoSame{})), nativeFact(6); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("TwoSame.b", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(TwoSame{}.B)), nativeFact(9); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("TwoSame.x", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(TwoSame{}.X)), nativeFact(10); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Mixed.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Mixed{})), nativeFact(11); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Mixed.x", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Mixed{}.X)), nativeFact(16); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Single.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Single{})), nativeFact(17); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Nested.e", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Nested[Inner, Empty]{}.E)), nativeFact(22); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Reuse.z", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Reuse[Tail]{}.Z)), nativeFact(28); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Reuse.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Reuse[Tail]{})), nativeFact(26); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Different.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(Pair[Empty, Empty2]{})), nativeFact(51); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("IntEmpty.b", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Pair[int32, Empty]{}.B)), nativeFact(50); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("Wrapped.x", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(Wrapped{}.X)), nativeFact(33); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("EmptyArray.size", func(t *testing.T) {
		if got, want := uint64(unsafe.Sizeof(EmptyArray{})), nativeFact(39); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
	t.Run("EmptyArray.x", func(t *testing.T) {
		if got, want := uint64(unsafe.Offsetof(EmptyArray{}.X)), nativeFact(41); got != want {
			t.Errorf("AUDIT_PADDING Go=%d C++=%d", got, want)
		}
	})
}
