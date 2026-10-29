package probe

import (
	"testing"
	"unsafe"
)

func TestTypeAvailable(t *testing.T) { var x A; t.Log(unsafe.Sizeof(x)) }
