package main

import "unsafe"

//llgo:pack 2
type Packed[T any] struct {
	A byte
	X T
}

//go:noinline
func measure[T any](v Packed[T]) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func main() { v := measure(Packed[int32]{}); println(v[0], v[1], v[2]) }
