package probe

import "testing"

func TestBitfieldControl(t *testing.T) {
	var x Basic
	x.XGof_set_a(1)
	x.XGof_set_b(-2)
	x.XGof_set_c(9)
	if x.XGof_get_a() != 1 || x.XGof_get_b() != -2 || x.XGof_get_c() != 9 {
		t.Fatal("AUDIT_CONTROL bit-field round trip")
	}
}
