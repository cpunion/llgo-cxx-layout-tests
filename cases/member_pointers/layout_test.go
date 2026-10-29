package probe

import (
	"testing"
	"unsafe"
)

func TestTypeAvailable(t *testing.T) { var x Holder; t.Log(unsafe.Sizeof(x)) }
