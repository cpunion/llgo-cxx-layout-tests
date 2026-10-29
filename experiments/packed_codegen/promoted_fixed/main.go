package main

import "unsafe"

type Inner struct {
	A byte
	X int32
}
type Outer struct {
	Prefix byte
	Inner
}

//go:noinline
func measure(v Outer) [3]uintptr {
	return [3]uintptr{unsafe.Sizeof(v), unsafe.Alignof(v), unsafe.Offsetof(v.X)}
}
func main() {
	v := measure(Outer{})
	println(v[0], v[1], v[2])
	if v != [3]uintptr{12, 4, 8} {
		panic("unexpected ordinary layout")
	}
}
