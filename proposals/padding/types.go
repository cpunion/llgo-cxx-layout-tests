package padding

// Transcriptions of #1029/#2788 mapping rules, not generated bindings.
type Empty struct{}
type Empty2 struct{}
type Bar2 struct {
	A, B int32
	//llgo:no-padding
	F Empty
}
type TwoSame struct {
	A Empty
	_ byte
	B Empty
	X int32
}
type Mixed struct {
	A Empty
	B Empty2
	_ byte
	C Empty
	X int32
}
type Single struct{ E Empty }
type Inner struct{ E Empty }
type Nested[T, U any] struct {
	Inner T
	//llgo:padding-if
	E U
	X int32
}
type Tail struct {
	X int64
	Y byte
}
type Reuse[T any] struct {
	//llgo:padding-if
	Value T
	Z     byte
}
type Pair[T, U any] struct {
	A T
	//llgo:padding-if
	B U
}
type Wrapper struct{ E Empty }
type Wrapped struct {
	W Wrapper
	X int32
}
type EmptyArray struct {
	E [5]Empty
	X int32
}
