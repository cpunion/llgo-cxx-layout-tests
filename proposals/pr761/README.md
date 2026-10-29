# PR #761 snapshot

This directory preserves actual generated output from llcppg commit
`fcfde2b6b240bfe8e470d363b412cbe79b7adf78` on macOS arm64 with libclang 22.1.8.
It is intentionally separate from main-generator cases: that PR's API and
runtime dependencies predate the main pin. These are **Itanium ABI** bindings,
not reusable MSVC bindings.

Run `llgo test -v ./proposals/pr761` on an Itanium target. The expected failures
compare native sizes and *real object* base/member addresses, not fabricated
pointer arithmetic. `collision/input.h` independently triggers field-name
collision in the PR generator. To regenerate against that historical checkout,
put each header at `cl/_testcpp/review_NAME/in.h`, then run
`llgo test ./cl -run '^TestCpp/review_NAME$'`: fixture output is saved as
`out.go.txt`. The missing golden causes a fixture failure; the layout test and
explicit generator panic, rather than that golden diff, are the bug evidence.
