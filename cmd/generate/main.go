package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/goplus/gogen/packages"
	"github.com/goplus/llcppg/cl"
	"github.com/goplus/llcppg/clang"
	clangc "github.com/llarhub/clang-c"
)

func main() {
	header := flag.String("header", "", "input header")
	output := flag.String("output", "", "generated Go file")
	language := flag.String("language", "c", "c or c++")
	target := flag.String("target", "", "Clang target triple")
	standard := flag.String("std", "", "language standard")
	flag.Parse()
	fmt.Println("libclang:", clang.GoStringAndDispose(clangc.GetClangVersion()))
	if *header == "" || *output == "" {
		panic("-header and -output are required")
	}
	abs, err := filepath.Abs(*header)
	if err != nil {
		panic(err)
	}
	idx := clang.CreateIndex(1, 1)
	defer idx.Dispose()
	args := []string{"-x", *language, "-fparse-all-comments"}
	if *target != "" {
		args = append(args, "--target="+*target)
	}
	if *standard != "" {
		args = append(args, "-std="+*standard)
	}
	tu, err := idx.ParseTranslationUnit(clang.DetailedPreprocessingRecord, abs, args...)
	if err != nil {
		panic(err)
	}
	defer tu.Dispose()
	lang := cl.LanguageC
	if *language == "c++" {
		lang = cl.LanguageCXX
	}
	root, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	pkg, err := cl.NewPackage("github.com/cpunion/llgo-cxx-layout-tests/probe", "probe", []cl.Source{tu}, &cl.Config{
		Language:      lang,
		Importer:      packages.NewImporter(nil, root),
		PubFileLookup: func(string) (string, bool) { return "", false },
		PackageOf: func(file string) (string, bool) {
			return "github.com/cpunion/llgo-cxx-layout-tests/probe", filepath.Clean(file) == abs
		},
	})
	if err != nil {
		panic(err)
	}
	if err := os.MkdirAll(filepath.Dir(*output), 0755); err != nil {
		panic(err)
	}
	f, err := os.Create(*output)
	if err != nil {
		panic(err)
	}
	if err := pkg.WriteTo(f); err != nil {
		panic(err)
	}
	if err := f.Close(); err != nil {
		panic(err)
	}
	fmt.Println(*output)
}
