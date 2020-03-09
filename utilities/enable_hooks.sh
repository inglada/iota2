#!/usr/bin/env python3

import os, sys, stat

src_dir = os.path.dirname(os.path.realpath(__file__))
dst_hooks = os.path.join(src_dir, "..", ".git", "hooks", "pre-commit")
if os.path.islink(dst_hooks):
    os.unlink(dst_hooks)
os.symlink(os.path.join(src_dir, "pre-commit"), dst_hooks)