# C/C++ layout and LLGo compatibility laboratory

This repository contains reproducible layout and ABI experiments for
[llcppg #1029](https://github.com/goplus/llcppg/issues/1029),
[LLGo #2788](https://github.com/xgo-dev/llgo/issues/2788), and the implementations
that those proposals depend on.

The investigation separates language guarantees, platform ABI requirements,
compiler behavior, binding generation, and LLGo storage/access/calls. A matching
`sizeof` is not evidence that offsets, accessors, virtual dispatch, or by-value
calls are compatible.

The report and test matrix are being assembled. Results record exact compiler
versions and distinguish native execution, emulation, cross-compilation,
expected conformance failures, and unsupported features. A known failing Go
test remains a failing test; the collection runner may classify its documented
failure as XFAIL without hiding the output.

Traditional object layout and inheritance are the first priority. Templates,
generic mappings, concepts, and newer language features follow separately.
