package main

import (
	"flag"
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"golang.org/x/tools/go/ssa"
	"golang.org/x/tools/go/ssa/ssautil"
	"os"
	"sort"
)

const source = `package example
import "unsafe"
//llgo:packed
type P struct { A byte; X int32 }
type S[T any] struct { A byte; X T }
func Fixed() (uintptr,uintptr,uintptr) {var p P; return unsafe.Sizeof(p),unsafe.Alignof(p),unsafe.Offsetof(p.X)}
func Generic[T any](x T) (uintptr,uintptr,uintptr) {s:=S[T]{X:x}; return unsafe.Sizeof(s),unsafe.Alignof(s),unsafe.Offsetof(s.X)}
func Use() (uintptr,uintptr,uintptr) { return Generic(int32(1)) }
`

type packedSizes struct{ types.Sizes }

func isP(t types.Type) bool { n, ok := t.(*types.Named); return ok && n.Obj().Name() == "P" }
func (s packedSizes) Sizeof(t types.Type) int64 {
	if isP(t) {
		return 5
	}
	return s.Sizes.Sizeof(t)
}
func (s packedSizes) Alignof(t types.Type) int64 {
	if isP(t) {
		return 1
	}
	return s.Sizes.Alignof(t)
}
func (s packedSizes) Offsetsof(fields []*types.Var) []int64 {
	if len(fields) == 2 && fields[0].Name() == "A" && fields[1].Name() == "X" {
		return []int64{0, 1}
	}
	return s.Sizes.Offsetsof(fields)
}
func main() {
	mode := flag.String("sizes", "gc", "gc, llgo, or custom")
	flag.Parse()
	fs := token.NewFileSet()
	file, err := parser.ParseFile(fs, "example.go", source, parser.ParseComments)
	if err != nil {
		panic(err)
	}
	sizes := types.SizesFor(*mode, "amd64")
	if *mode == "custom" {
		sizes = packedSizes{types.SizesFor("gc", "amd64")}
	}
	if sizes == nil {
		panic("SizesFor returned nil")
	}
	conf := types.Config{Importer: importer.Default(), Sizes: sizes}
	info := types.Info{Types: map[ast.Expr]types.TypeAndValue{}, Defs: map[*ast.Ident]types.Object{}, Uses: map[*ast.Ident]types.Object{}, Selections: map[*ast.SelectorExpr]*types.Selection{}, Instances: map[*ast.Ident]types.Instance{}}
	pkg, err := conf.Check("example", fs, []*ast.File{file}, &info)
	if err != nil {
		panic(err)
	}
	ast.Inspect(file, func(n ast.Node) bool {
		if c, ok := n.(*ast.CallExpr); ok {
			if sel, ok := c.Fun.(*ast.SelectorExpr); ok {
				fmt.Printf("typecheck line=%d %s value=%v\n", fs.Position(c.Pos()).Line, sel.Sel.Name, info.Types[c].Value)
			}
		}
		return true
	})
	prog := ssa.NewProgram(fs, ssa.InstantiateGenerics|ssa.SanityCheckFunctions)
	for _, imp := range pkg.Imports() {
		prog.CreatePackage(imp, nil, nil, true)
	}
	sp := prog.CreatePackage(pkg, []*ast.File{file}, &info, true)
	sp.Build()
	functions := []*ssa.Function{}
	for fn := range ssautil.AllFunctions(prog) {
		if fn.Pkg == sp || fn.Origin() != nil && fn.Origin().Pkg == sp {
			functions = append(functions, fn)
		}
	}
	sort.Slice(functions, func(i, j int) bool { return functions[i].String() < functions[j].String() })
	for _, fn := range functions {
		fn.WriteTo(os.Stdout)
	}
	fixed := sp.Func("Fixed")
	for _, b := range fixed.Blocks {
		for _, in := range b.Instrs {
			if ret, ok := in.(*ssa.Return); ok {
				for _, v := range ret.Results {
					if _, ok := v.(*ssa.Const); !ok {
						panic("Fixed returned a nonconstant")
					}
				}
			}
		}
	}
}
