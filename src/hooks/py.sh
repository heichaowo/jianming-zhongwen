#!/bin/sh
# Find a Python 3 and exec the hook script with it. Same probe order as the
# official security-guidance plugin: python3, python, py -3. On Windows,
# python3 is often the Microsoft Store stub, which fails the probe and falls
# through to a python.org install or the py launcher. The hooks are advisory,
# so with no interpreter the shim says so once on stderr and exits 0.
for cmd in python3 python "py -3"; do
    # shellcheck disable=SC2086
    v=$($cmd -c 'import sys; print(sys.version_info[0])' 2>/dev/null </dev/null) || continue
    if [ "$v" = "3" ]; then
        # shellcheck disable=SC2086
        exec $cmd "$@"
    fi
done
echo "jianming-zhongwen: no Python 3 found (tried python3, python, py -3); the hooks are off" >&2
exit 0
