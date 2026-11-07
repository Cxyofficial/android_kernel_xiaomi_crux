#!/usr/bin/env python3
"""Make SukiSU-Ultra (builtin branch) compile against this 4.14 tree with SUSFS v2.2.0."""
import re, sys, pathlib

KSU = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "drivers/kernelsu")

def patch(path, old, new, count=1):
    p = KSU / path
    s = p.read_text()
    if new in s:
        print(f"[skip] {path}")
        return
    if old not in s:
        sys.exit(f"[fail] pattern not found in {path}")
    p.write_text(s.replace(old, new, count))
    print(f"[ok] {path}")

# 1) linux/static_call.h appeared in 5.10
patch("kernel_includes.h",
      "#include <linux/static_call.h>",
      "#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)\n#include <linux/static_call.h>\n#endif")

# 2) <vdso/datapage.h> appeared in 5.2; cpu_spoof needs the vdso_data layout
p = KSU / "extension/cpu_spoof.c"
s = p.read_text()
if "4.14 compat: no <vdso/datapage.h>" not in s:
    s = s.replace("#include <linux/kernel.h>",
                  "#include <linux/kernel.h>\n"
                  "/* 4.14 compat: no <vdso/datapage.h> / vdso_data before 5.2 */\n"
                  "#if LINUX_VERSION_CODE < KERNEL_VERSION(5, 2, 0)\n"
                  "#include <linux/errno.h>\n"
                  "int ksu_extension_cpu_spoof_io(u32 id, void __user *raw)\n"
                  "{\n\treturn -EOPNOTSUPP;\n}\n#else", 1)
    s = s.rstrip() + "\n#endif /* LINUX_VERSION_CODE < 5.2.0 */\n"
    p.write_text(s)
    print("[ok] extension/cpu_spoof.c")

# 3) KPM's kallsyms based struct poking is GKI only
patch("ksu_main.c",
      '#include "extension/kpm.c"\n#include "extension/kpm/kpm.c"\n#include "extension/kpm/compact.c"\n#include "extension/kpm/super_access.c"',
      '#include "extension/kpm.c"\n'
      '/* KPM dynamic struct access is kallsyms/GKI only, does not build on 4.14 */\n'
      '#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 10, 0)\n'
      '#include "extension/kpm/kpm.c"\n#include "extension/kpm/compact.c"\n#include "extension/kpm/super_access.c"\n#endif')

# 4) SUSFS v2.2.0 has no priority-uid-filter command
patch("supercall/dispatch.c",
      '        case CMD_SUSFS_SET_PRIORITY_UID_FILTER:\n            susfs_set_priority_uid_filter(arg);\n            return 0;',
      '#if 0 /* SUSFS v2.3+ only; this kernel ships SUSFS v2.2.0 */\n'
      '        case CMD_SUSFS_SET_PRIORITY_UID_FILTER:\n            susfs_set_priority_uid_filter(arg);\n            return 0;\n#endif')

# 5) shim header + hook it into the common include block
shim = KSU / "susfs_sukisu_compat.h"
if not shim.exists():
    shim.write_text(pathlib.Path(__file__).with_name("susfs_sukisu_compat.h").read_text())
    print("[ok] susfs_sukisu_compat.h")

patch("kernel_includes.h",
      "#ifdef CONFIG_KSU_SUSFS\n#include <linux/susfs.h>\n#include <linux/susfs_def.h>\n#endif",
      "#ifdef CONFIG_KSU_SUSFS\n#include <linux/susfs.h>\n#include <linux/susfs_def.h>\n#include \"susfs_sukisu_compat.h\"\n#endif")

# 6) SELinux AVD registration hook is SUSFS v2.3+ only
patch("selinux/sepolicy.c",
      "extern int susfs_add_sus_avd_allowed_by_type(u32 s_type, u32 t_type, u16 type, u32 orig_avd_allowed);",
      "/* SUSFS v2.3+ hook; the vendored SUSFS v2.2.0 has no such entry point. */\n"
      "static inline int susfs_add_sus_avd_allowed_by_type(u32 s_type, u32 t_type, u16 type, u32 orig_avd_allowed)\n"
      "{\n\treturn 0;\n}")

print("done")
