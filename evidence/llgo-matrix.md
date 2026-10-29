# LLGo 原生运行矩阵

固定 main 版本，每个平台重新生成或使用注明目标的 Linux 交叉生成结果。XFAIL 是实际失败；不是 PASS。

| case | aarch64-unknown-linux-gnu | arm64-apple-darwin | x86_64-apple-darwin | x86_64-unknown-linux-gnu |
|---|---|---|---|---|
| aligned_plain | XFAIL | XFAIL | XFAIL | XFAIL |
| atomic_member | XFAIL | XFAIL | XFAIL | XFAIL |
| base_bits | XFAIL | XFAIL | XFAIL | XFAIL |
| basic_bits | PASS | PASS | PASS | PASS |
| bit_align | XFAIL | XFAIL | XFAIL | XFAIL |
| bit_callback | XFAIL | XFAIL | XFAIL | XFAIL |
| bit_nested | XFAIL | XFAIL | XFAIL | XFAIL |
| bool_typedef | XFAIL | XFAIL | XFAIL | XFAIL |
| concept_specialization | XFAIL | XFAIL | XFAIL | XFAIL |
| covariant | XFAIL | XFAIL | XFAIL | XFAIL |
| empty_nua | XFAIL | XFAIL | XFAIL | XFAIL |
| empty_plain | XFAIL | XFAIL | XFAIL | XFAIL |
| flexible | XFAIL | XFAIL | XFAIL | XFAIL |
| member_pointers | XFAIL | XFAIL | XFAIL | XFAIL |
| nontrivial_value | XFAIL | XFAIL | XFAIL | XFAIL |
| nonvirtual_tail | XFAIL | XFAIL | XFAIL | XFAIL |
| packed_plain | XFAIL | XFAIL | XFAIL | XFAIL |
| template_specialization | XFAIL | XFAIL | XFAIL | XFAIL |
| union_bits | XFAIL | XFAIL | XFAIL | XFAIL |
| union_hfa | XFAIL | XFAIL | XFAIL | XFAIL |
