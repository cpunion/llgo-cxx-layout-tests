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
func measure[T any](v Outer[T]) uintptr { return unsafe.Offsetof(v.X) }
func main() {
	v := measure(Outer[int32]{})
	println(v)
	if v != 8 {
		panic("unexpected promoted field offset")
	}
}
