package main

import (
	"reflect"
	"unsafe"
)

type Tail struct {
	B byte
	Z struct{}
}

func size[T any]() uintptr { return unsafe.Sizeof(*new(T)) }

func main() {
	var f func()
	var v Tail
	var a [2]Tail
	println("func: constant / reflect / reflect-pointer-element", unsafe.Sizeof(f), reflect.TypeOf(f).Size(), reflect.TypeOf(&f).Elem().Size())
	println("tail: constant / generic / reflect", unsafe.Sizeof(v), size[Tail](), reflect.TypeOf(v).Size())
	println("tail-array: constant / stride", unsafe.Sizeof(a), uintptr(unsafe.Pointer(&a[1]))-uintptr(unsafe.Pointer(&a[0])))
}
