package probe

import (
	"testing"
	"unsafe"
)

func TestTypeAvailable(t *testing.T) { var x AtomicMember; t.Log(unsafe.Sizeof(x)) }
