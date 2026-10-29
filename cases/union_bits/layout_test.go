package probe

import "testing"

func TestUnionBitfield(t *testing.T) {
	var x UnionBits
	*x.XGof_ref_raw() = 0xa4
	*x.XGof_ref_a() = 1
	if got := *x.XGof_ref_raw(); got != 0xa5 {
		t.Errorf("AUDIT_UNION_BITS got=%#x want=0xa5", got)
	}
}
