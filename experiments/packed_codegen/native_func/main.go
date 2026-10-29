package main

import "unsafe"

//llgo:cdecl
type Native func()

//go:noinline
func measure[T any](v T) uintptr { return unsafe.Sizeof(v) }
func main()                      { var v Native; println(measure(v)) }
