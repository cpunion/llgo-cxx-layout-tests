package main

import "unsafe"

type Inner[T any] struct {
	A byte
	X T
}
type Outer[T any] struct {
	Prefix byte
	Inner[T]
}

//go:noinline
func measure[T any](v Outer[T]) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func main() { v := measure(Outer[int32]{}); println(v[0], v[1], v[2]) }
