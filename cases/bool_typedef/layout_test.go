package probe

import "testing"

func TestBoolAlias(t *testing.T) {
	var x AliasBits
	x.XGof_set_enabled(true)
	if !x.XGof_get_enabled() {
		t.Fatal("AUDIT_BOOL lost true")
	}
}
