/* SPDX-License-Identifier: GPL-2.0 */
/*
 * SukiSU-Ultra <-> SUSFS v2.2.0 compatibility shim.
 *
 * SukiSU-Ultra (builtin branch) expects a handful of entry points that only
 * exist in newer SUSFS kernel patches (v2.3+). This kernel ships SUSFS
 * v2.2.0, so we provide equivalent (or safely inert) implementations here
 * instead of touching the vendored SUSFS code.
 */
#ifndef __KSU_SUSFS_SUKISU_COMPAT_H
#define __KSU_SUSFS_SUKISU_COMPAT_H

#include <linux/types.h>
#include <linux/sched.h>
#include <linux/thread_info.h>
#include <linux/cred.h>

/* free TIF slots on this 4.14 tree: 26..32 (33 is TIF_PROC_UMOUNTED) */
#ifndef TIF_PROC_NO_SU
#define TIF_PROC_NO_SU 26
#endif
#ifndef TIF_PROC_UMOUNTED_ZYGOTE_NEXT
#define TIF_PROC_UMOUNTED_ZYGOTE_NEXT 27
#endif

/* "this task must not gain root" marker used by newer SUSFS */
static inline void susfs_set_current_proc_no_su(void)
{
	set_ti_thread_flag(&current->thread_info, TIF_PROC_NO_SU);
}

static inline bool susfs_is_current_proc_no_su(void)
{
	return test_ti_thread_flag(&current->thread_info, TIF_PROC_NO_SU);
}

/*
 * Newer SUSFS keeps a separate flag for processes forked through the
 * zygote_next path. v2.2.0 has no consumer for it, so record the flag only.
 */
static inline void susfs_set_current_proc_umounted_for_zygote_next(void)
{
	set_ti_thread_flag(&current->thread_info, TIF_PROC_UMOUNTED_ZYGOTE_NEXT);
}

/* string helpers: v2.2.0 defines susfs_starts_with() in fs/susfs.c (unexported) */
extern bool susfs_starts_with(const char *str, const char *prefix);

static inline bool susfs_ends_with(const char *str, const char *suffix)
{
	size_t slen = strlen(str);
	size_t tlen = strlen(suffix);

	if (tlen > slen)
		return false;
	return !memcmp(str + slen - tlen, suffix, tlen);
}

/* priority-app uid filter (v2.3+ feature); inert on v2.2.0 */
static inline void susfs_set_priority_uid_filter(void __user *arg)
{
	(void)arg;
}

static inline void susfs_parse_priority_app_strings(void)
{
}

#endif /* __KSU_SUSFS_SUKISU_COMPAT_H */
