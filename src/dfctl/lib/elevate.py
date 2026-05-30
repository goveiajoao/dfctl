import os
import sys
from pathlib import Path


def elevate():
    os.execv(
        "/usr/bin/sudo",
        [
            "sudo",
            "-E",
            "env",
            f"HOME={os.environ['HOME']}",
            sys.executable,
            str(Path(sys.prefix, "bin", "dfctl")),
            *sys.argv[1:],
            "--uid",
            str(os.getuid()),
        ],
    )


def go_to_user(uid: int, gid: int):
    try:
        os.setgid(gid)
        # os.setgroups([])
        os.setuid(uid)
    except Exception as e:
        print(e)
