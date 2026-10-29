package probe

import "testing"

func TestNontrivialABI(t *testing.T) {
	// Native ABI passes a pointer to the nontrivial argument. The oracle only
	// returns the address: it never dereferences the mismatched Go integer.
	got := _AcceptNontrivial(Nontrivial{Value: 37})
	if got == 37 {
		t.Errorf("AUDIT_NONTRIVIAL native argument address equals Go integer payload: %d", got)
	}
}
