package main

import "unsafe"

type Inner[T any] struct {
	A byte
	X T
}

//go:noinline
func measure[T any](v Inner[T]) uintptr { return unsafe.Offsetof(v.X) }
func main() {
	v := measure(Inner[int32]{})
	println(v)
	if v != 4 {
		panic("unexpected direct field offset")
	}
}
