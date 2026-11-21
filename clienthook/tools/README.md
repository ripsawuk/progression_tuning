# `clienthook\tools`

The offline proof for the hook, and the read-only readers used to derive it. Every driver here compiles the
shipped unit it tests - the same `.c` files `build.cmd` compiles - so what is proven is what runs.

## First

    clienthook\build.cmd
    clienthook\tools\build_tests.cmd          -> build\*_test.exe, build\ch_passthru_host.exe
    python -I clienthook\tools\test_build24.py

`test_build24.py` is the tree's general proof: the artefact and its pin, two clean builds byte-identical, the
source tree, the image's strings, the package scan, the client's own bytes, and every driver below.

## Drivers, and the harness that runs them

| driver (`tools\*.c` -> `build\*.exe`) | unit under test | harness |
|---|---|---|
| `g11_test.c` | `src\g11.c` | `test_g11.py` |
| `master_test.c` | `src\master.c` + `src\resolve.c` | `test_master.py` |
| `detour_test.c` | `src\master.c` + `src\resolve.c` | `test_detour.py` |
| `pubxp_test.c` | `src\pubxp.c` | `test_build24.py` |
| `publish_test.c` | `src\publish.c` | `test_build24.py` |
| `tokens_test.c` | `src\tokens.c` + `src\g11.c` | `test_build24.py` |
| `pick_test.c` | `src\pick.c` + `src\g11.c` + `src\resolve.c` | `test_build24.py` |
| `armory_test.c` | `src\armory.c` + `src\g11.c` + `src\resolve.c` | `test_build24.py` |
| `nativepay_test.c` | `src\nativepay.c` + `src\resolve.c` | `test_nativepay.py`, `test_build24.py` |
| `resolve_check.c` | `src\resolve.c`, over a PE file on disk | `test_resolve.py` |
| `guard_test.c` | the shipped `src\proxy_main.c` | `test_build24.py` |
| `passthru_host.c` | loads the built DLL (its name is the point) | `test_nativepay.py`, `test_build24.py` |
| `logline_test.c` | the shipped `src\proxy_main.c`, included outright | **none - run it by hand**, see below |

    python -I clienthook\tools\test_proxy.py      -> pass-through: OK - identical (no game folder needed)
    python -I clienthook\tools\test_g11.py
    python -I clienthook\tools\test_master.py
    python -I clienthook\tools\test_detour.py
    python -I clienthook\tools\test_nativepay.py
    python -I clienthook\tools\test_resolve.py    -> needs KRONOS_GAME_DIR (it reads the client file)

`test_resolve.py` skips with a `SKIP` line and exits 0 when no game folder is configured; the rest need only the
build.

`logline_test.exe` has no Python harness: the bounded log line is static, so the only way to call it with an
over-long text is from its own translation unit. Run it and read the last line:

    clienthook\build\logline_test.exe             -> logline: OK - 10 checks

## The read-only readers

None of these writes to the game folder; each prints what it read.

| tool | what it answers |
|---|---|
| `pe_rva.py` | sections, rva -> file bytes, and what an rva lands in |
| `pe_imports.py` | a PE's static and delay imports (which module can we stand in front of) |
| `disfn.py` | disassemble a byte range of a PE's `.text` |
| `find_xrefs.py` | code that references a string in a PE, by linear disassembly |
| `xref_call.py` | every reference a PE's code or data makes to one rva |
| `unwind.py` | the UNWIND_INFO a PE holds for an rva (`--prove`: the section and protection) |
| `minidump_info.py` | a minidump: modules, the exception record, threads, a stack walk |
| `gen_def.py` | the `.def` that forwards every export of a system DLL to a renamed copy of itself |
