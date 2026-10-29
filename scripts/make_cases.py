"""Maintain independent native oracles and executable Go assertions (no hand-built layouts)."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'cases'
# Native expressions, generated Go expressions: actual oracle is the target C compiler.
layout={
 'bit_nested': [('sizeof(struct Packet)','unsafe.Sizeof(Packet{})'),('__builtin_offsetof(struct Packet,payload)','unsafe.Offsetof(Packet{}.Payload)')],
 'base_bits': [('sizeof(Derived)','unsafe.Sizeof(Derived{})'),('__builtin_offsetof(Derived,tail)','unsafe.Offsetof(Derived{}.Tail)')],
 'bit_align': [('sizeof(struct Flags16)','unsafe.Sizeof(Flags16{})'),('__alignof__(struct Flags16)','unsafe.Alignof(Flags16{})'),('sizeof(struct Container)','unsafe.Sizeof(Container{})'),('__builtin_offsetof(struct Container,flags)','unsafe.Offsetof(Container{}.Flags)'),('__builtin_offsetof(struct Container,suffix)','unsafe.Offsetof(Container{}.Suffix)')],
 'bit_callback': [('sizeof(struct CallbackBits)','unsafe.Sizeof(CallbackBits{})'),('__builtin_offsetof(struct CallbackBits,callback)','unsafe.Offsetof(CallbackBits{}.Callback)'),('sizeof(((struct CallbackBits*)0)->callback)','unsafe.Sizeof(CallbackBits{}.Callback)')],
 'flexible': [('sizeof(struct Flexible)','unsafe.Sizeof(Flexible{})'),('__builtin_offsetof(struct Flexible,data)','unsafe.Offsetof(Flexible{}.Data)')],
}
for name,pairs in layout.items():
 d=R/name; lang=(d/'language').read_text().strip(); ext='cpp' if lang=='c++' else 'c'
 body='#include "../input.h"\n'+('extern "C" ' if ext=='cpp' else '')+'unsigned long long audit_fact(int i) {\n const unsigned long long v[] = {'+', '.join(x[0] for x in pairs)+'}; return v[i];\n}\n'
 (d/'_native').mkdir(exist_ok=True); (d/'_native'/('oracle.'+ext)).write_text(body)
 (d/'bridge.go').write_text('package probe\nimport _ "unsafe"\nconst LLGoFiles = "_native/oracle.'+ext+'"\n//go:linkname nativeFact C.audit_fact\nfunc nativeFact(i int32) uint64\n')
 tests='package probe\nimport("testing";"unsafe";"reflect")\nfunc TestNativeLayout(t *testing.T) {\n'
 for i,(ce,ge) in enumerate(pairs):
  tests+=f' if got,want:=uint64({ge}),nativeFact({i}); got!=want {{ t.Errorf("AUDIT_LAYOUT {ce}: Go=%d C=%d",got,want) }}\n'
 typ={'bit_nested':'Packet','base_bits':'Derived','bit_align':'Flags16','bit_callback':'CallbackBits','flexible':'Flexible'}[name]
 tests+=f' if got,want:=uint64(reflect.TypeOf({typ}{{}}).Size()),nativeFact(0); got!=want {{ t.Errorf("AUDIT_REFLECT {typ}: Go=%d C=%d",got,want) }}\n}}\n'
 (d/'layout_test.go').write_text(tests)
(R/'bool_typedef'/'layout_test.go').write_text('''package probe
import "testing"
func TestBoolAlias(t *testing.T) { var x AliasBits; x.XGof_set_enabled(true); if !x.XGof_get_enabled() { t.Fatal("AUDIT_BOOL lost true") } }
''')
(R/'union_bits'/'layout_test.go').write_text('''package probe
import "testing"
func TestUnionBitfield(t *testing.T) { var x UnionBits; *x.XGof_ref_raw()=0xa4; *x.XGof_ref_a()=1; if got:=*x.XGof_ref_raw();got!=0xa5 { t.Errorf("AUDIT_UNION_BITS got=%#x want=0xa5",got) } }
''')
d=R/'union_hfa';(d/'_native').mkdir(exist_ok=True)
(d/'_native/oracle.c').write_text('''#include "../input.h"
union FloatUnion round_union(union FloatUnion x) { x.a.x+=1; x.a.y+=2; return x; }
unsigned long long audit_fact(int i) { const unsigned long long v[]={sizeof(union FloatUnion), __alignof__(union FloatUnion)}; return v[i]; }
''')
(d/'bridge.go').write_text('''package probe
import _ "unsafe"
const LLGoFiles = "_native/oracle.c"
//go:linkname round C.round_union
func round(x FloatUnion) FloatUnion
//go:linkname nativeFact C.audit_fact
func nativeFact(i int32) uint64
''')
(d/'layout_test.go').write_text('''package probe
import("testing";"unsafe")
func TestUnionABI(t *testing.T) {
 var x FloatUnion
 if got,want:=uint64(unsafe.Sizeof(x)),nativeFact(0);got!=want { t.Fatalf("AUDIT_LAYOUT size Go=%d C=%d",got,want) }
 if got,want:=uint64(unsafe.Alignof(x)),nativeFact(1);got!=want { t.Fatalf("AUDIT_LAYOUT align Go=%d C=%d",got,want) }
 x.XGof_ref_a().X=3; x.XGof_ref_a().Y=5
 y:=round(x)
 if y.XGof_ref_a().X!=4 || y.XGof_ref_a().Y!=7 { t.Errorf("AUDIT_HFA got=(%v,%v) want=(4,7)",y.XGof_ref_a().X,y.XGof_ref_a().Y) }
}
''')
d=R/'covariant'; (d/'_native').mkdir(exist_ok=True)
(d/'_native/oracle.cpp').write_text('''#include "../input.h"
static ReturnDerived result;
ReturnBase* FactoryBase::make() { return &result; }
int FactoryBase::base_after() { return 11; }
ReturnDerived* FactoryDerived::make() { return &result; }
int FactoryDerived::derived_after() { return 22; }
extern "C" FactoryDerived* get_factory() { static FactoryDerived f; return &f; }
extern "C" ReturnDerived* get_result() { return &result; }
''')
(d/'bridge.go').write_text('''package probe
import _ "unsafe"
const LLGoFiles = "_native/oracle.cpp"
//go:linkname create C.get_factory
func create() *FactoryDerived
//go:linkname expected C.get_result
func expected() *ReturnDerived
''')
(d/'layout_test.go').write_text('''package probe
import("testing";"unsafe")
func TestCovariant(t *testing.T) {
 f:=create(); got:=f.XGo_vptr().Make(f); want:=expected()
 if got!=want { t.Errorf("AUDIT_COVARIANT pointer delta=%d want=0",int64(uintptr(unsafe.Pointer(got))-uintptr(unsafe.Pointer(want)))) }
}
''')
# Positive controls stop an all-failing environment from looking like reproduced bugs.
d=R/'basic_bits'; d.mkdir(exist_ok=True)
(d/'input.h').write_text('struct Basic { unsigned a:1; signed b:3; unsigned c:4; };\n')
(d/'language').write_text('c\n')
(d/'layout_test.go').write_text('''package probe
import "testing"
func TestBitfieldControl(t *testing.T) { var x Basic; x.XGof_set_a(1); x.XGof_set_b(-2); x.XGof_set_c(9); if x.XGof_get_a()!=1 || x.XGof_get_b()!=-2 || x.XGof_get_c()!=9 { t.Fatal("AUDIT_CONTROL bit-field round trip") } }
''')
