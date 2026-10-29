package probe

import (
	"testing"
	"unsafe"
)

func TestTypeAvailable(t *testing.T) { var x B; t.Log(unsafe.Sizeof(x)) }
