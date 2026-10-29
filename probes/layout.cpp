// Freestanding: no standard-library or SDK headers are needed for cross compilation.
struct Empty {};
struct Empty2 {};
struct Bar2 { int a, b; [[no_unique_address]] Empty f; };
struct TwoSame { [[no_unique_address]] Empty a, b; int x; };
struct Mixed { [[no_unique_address]] Empty a; [[no_unique_address]] Empty2 b; [[no_unique_address]] Empty c; int x; };
struct Single { Empty e; };
struct Inner { [[no_unique_address]] Empty e; };
struct Nested { [[no_unique_address]] Inner inner; [[no_unique_address]] Empty e; int x; };
struct Tail { long long x; char y; Tail() : x(0), y(0) {} };
struct Reuse { [[no_unique_address]] Tail value; char z; };
struct Wrapper { Empty e; };
struct Wrapped { [[no_unique_address]] Wrapper w; int x; };
struct alignas(16) AlignedEmpty {};
struct AlignedMember { AlignedEmpty e; char c; };
struct EmptyArray { Empty e[5]; int x; };
struct Ref { int &value; };
template<class T, class U> struct Pair { [[no_unique_address]] T a; [[no_unique_address]] U b; };
using EmptyInt = Pair<Empty, int>;
using IntEmpty = Pair<int, Empty>;
using Different = Pair<Empty, Empty2>;
struct BitsABI { unsigned a:3; unsigned long long b:40; char tail; };
struct PackedABI { char lead; unsigned a:3; unsigned :0; unsigned short b:9; int value; } __attribute__((packed));
struct ScalarABI { char lead; long number; double value; void *pointer; };
#pragma pack(push, 1)
struct PragmaPacked { char c; double d; };
#pragma pack(pop)
struct alignas(16) AlignedPacked { char c; int x; } __attribute__((packed));
struct BaseTail { int x; char c; BaseTail() : x(0), c(0) {} };
struct DerivedTail : BaseTail { char d; };
struct EmptyBase : Empty { int x; };
struct SameBaseMember : Empty { [[no_unique_address]] Empty e; int x; };
struct A { int a; };
struct L : virtual A { int l; };
struct R : virtual A { int r; };
struct D : L, R { int d; };
struct E : D { long long e; };
struct PlainL : A { int l; };
struct PlainR : A { int r; };
struct PlainD : PlainL, PlainR { int d; };
struct V { virtual int value() { return 7; } };
struct VirtualPrimary : virtual V { int a; };
struct Other { int x; };
struct PrimaryOrder : Other, L {};
struct MemberSingle { int x; void f(); };
struct MemberMultiple : Other, MemberSingle {};
struct MemberVirtual : virtual MemberSingle {};
struct Trivial { int x; };
struct Nontrivial { int x; ~Nontrivial() {} };
struct __attribute__((trivial_abi)) TrivialABI { int x; ~TrivialABI() {} };
template<class T> struct Special { T value; };
template<> struct Special<Empty> { long long cookie; };
template<class T> struct AlignedGeneric { alignas(T) char data[sizeof(T)]; };
#if __cplusplus >= 202002L
template<class T> concept Small = (sizeof(T) <= 4);
template<class T> struct Choice { T value; long long tag; };
template<Small T> struct Choice<T> { T value; };
#endif
#if defined(_MSC_VER)
struct MicrosoftNUA { [[msvc::no_unique_address]] Empty e; int x; };
#endif
// Stored values are evaluated after the whole declaration, including trailing attributes.
#define S(T) sizeof(T), alignof(T)
#define O(T,F) __builtin_offsetof(T,F)
extern "C" const unsigned long long audit_facts[] = {
 S(Empty), S(Bar2), O(Bar2,f), sizeof(Bar2::f),
 S(TwoSame), O(TwoSame,a), O(TwoSame,b), O(TwoSame,x),
 S(Mixed), O(Mixed,a), O(Mixed,b), O(Mixed,c), O(Mixed,x),
 S(Single), S(Nested), O(Nested,inner), O(Nested,e), O(Nested,x),
 S(Tail), S(Reuse), O(Reuse,z), S(Wrapper), S(Wrapped), O(Wrapped,x),
 S(AlignedEmpty), S(AlignedMember), O(AlignedMember,c), S(EmptyArray), O(EmptyArray,x),
 S(Ref), sizeof(((Ref*)0)->value), S(EmptyInt), O(EmptyInt,b), S(IntEmpty), O(IntEmpty,b), S(Different),
 S(BitsABI), O(BitsABI,tail), S(PackedABI), O(PackedABI,value),
 S(ScalarABI), O(ScalarABI,number), O(ScalarABI,value), S(PragmaPacked), O(PragmaPacked,d),
 S(AlignedPacked), O(AlignedPacked,x), S(BaseTail), S(DerivedTail), O(DerivedTail,d),
 S(EmptyBase), O(EmptyBase,x), S(SameBaseMember), O(SameBaseMember,e), O(SameBaseMember,x),
 S(L), S(R), S(D), S(E), S(PlainD), S(VirtualPrimary), O(VirtualPrimary,a), S(PrimaryOrder),
 sizeof(int MemberSingle::*), sizeof(void(MemberSingle::*)()),
 sizeof(int MemberMultiple::*), sizeof(void(MemberMultiple::*)()),
 sizeof(int MemberVirtual::*), sizeof(void(MemberVirtual::*)()),
 S(Trivial), S(Nontrivial), S(TrivialABI), S(Special<Empty>), S(AlignedGeneric<AlignedEmpty>),
#if __cplusplus >= 202002L
 S(Choice<int>), S(Choice<long long>),
#else
 0, 0, 0, 0,
#endif
#if defined(_MSC_VER)
 S(MicrosoftNUA), O(MicrosoftNUA,x)
#else
 0, 0, 0
#endif
};
static_assert(sizeof(Empty) >= 1, "complete empty objects have positive size");
static_assert(sizeof(AlignedEmpty) >= 16 && alignof(AlignedEmpty) == 16, "empty does not mean size one");
static_assert(sizeof(EmptyArray::e) == 5 * sizeof(Empty), "array stride uses complete object size");
static_assert(sizeof(((Ref*)0)->value) == sizeof(int), "reference expression denotes referent");
// Keep parameter/return classification in the IR, separate from layout facts.
extern "C" Trivial call_trivial(Trivial x) { return x; }
extern "C" Nontrivial call_nontrivial(Nontrivial x) { return x; }
extern "C" TrivialABI call_trivial_abi(TrivialABI x) { return x; }
#ifdef AUDIT_NATIVE
extern "C" int printf(const char*, ...);
template<class T, class U> long long delta(T *p, U *q) { return (char*)p - (char*)q; }
int main() {
 printf("{\"facts\":[");
 for (unsigned i=0; i<sizeof(audit_facts)/sizeof(*audit_facts); ++i) printf("%s%llu", i ? "," : "", audit_facts[i]);
 L l; D d; E e; VirtualPrimary v; PrimaryOrder p;
 PlainD n;
 printf("],\"dynamic\":{\"L.A\":%lld,\"D.L.A\":%lld,\"E.L.A\":%lld,\"D.R.A\":%lld,\"D.L\":%lld,\"D.R\":%lld,\"VirtualPrimary.V\":%lld,\"PrimaryOrder.Other\":%lld,\"PrimaryOrder.L\":%lld,\"PlainD.L.A\":%lld,\"PlainD.R.A\":%lld}}\n",
 delta((A*)&l,&l),delta((A*)(L*)&d,(L*)&d),delta((A*)(L*)&e,(L*)&e),delta((A*)(R*)&d,&d),delta((L*)&d,&d),delta((R*)&d,&d),delta((V*)&v,&v),delta((Other*)&p,&p),delta((L*)&p,&p),delta((A*)(PlainL*)&n,&n),delta((A*)(PlainR*)&n,&n));
 if ((A*)(L*)&d != (A*)(R*)&d) return 1;
 if ((A*)(PlainL*)&n == (A*)(PlainR*)&n) return 2;
 if (v.value() != 7) return 3;
 TwoSame t;
 if (&t.a == &t.b) return 4;
 return 0;
}
#endif
