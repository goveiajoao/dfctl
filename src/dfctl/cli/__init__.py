import argparse
import multiprocessing as mp
import os
import sys
from pathlib import Path

import dfctl.cli.cmd as cmd
from dfctl.lib.config import Config
from dfctl.lib.elevate import elevate
from dfctl.lib.target import sudo_level_in_argv


def cli(CONFIG):

    # Parser Section
    arguments_parser = argparse.ArgumentParser(add_help=False)
    arguments_parser.add_argument(
        "--noconfirm",
        action="store_true",
        help="skip confirmation prompts",
    )
    arguments_parser.add_argument(
        "--autopull",
        action="store_false",
        help="auto pull before any local-repo action",
    )
    arguments_parser.add_argument(
        "--autopush",
        action="store_false",
        help="auto push after any local-repo action",
    )
    arguments_parser.add_argument(
        "--uid",
        help=argparse.SUPPRESS,
    )
    arguments_parser.add_argument(
        "--gid",
        help=argparse.SUPPRESS,
    )

    class CustomArgumentParser(argparse.ArgumentParser):
        def error(self, message):
            CONFIG.gitter.exit()
            super().error(message)

    parser: argparse.ArgumentParser = CustomArgumentParser(
        prog="dfctl",
        description="Dotfiles CLI",
        color=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[arguments_parser],
        epilog="target:\n"
        "  [LEVEL@]([-]GROUP[:BRANCH][/INSTANCE][...] | [-]GROUP[...][:BRANCH][/INSTANCE])\n"
        "  elements:\n"
        "    LEVEL:     the ground where all your groups will live\n"
        "    GROUP:     the dotfile group itself, like 'tmux'\n"
        "    BRANCH:    the branch of the group, like 'main', 'secound', ...\n"
        "    INSTANCE:  index of a file or folder of the dot\n"
        "  comment:\n"
        "    Syntax for Lists (...): [a,b,c,d,...]\n"
        "    '*' Can be used in LEVEL and GROUP to expand all elements\n"
        "    '-' Means Exclude/Negate\n"
        "    '<x> target' Means that it is a target that accept info until x, if passed info after x, it will error\n",
    )

    subparsers: argparse._SubParsersAction = parser.add_subparsers(required=True)
    cmd.init(subparsers, CONFIG, arguments_parser)

    args = parser.parse_args()

    try:
        args.func(args)
    finally:
        CONFIG.gitter.exit()


def main():
    if os.getuid() == 0:
        if "--uid" not in "".join(sys.argv):
            raise Exception("please do not run as root")
    uid: int = (
        int(sys.argv[sys.argv.index("--uid") + 1])
        if "--uid" in "".join(sys.argv)
        else os.getuid()
    )
    gid: int = (
        int(sys.argv[sys.argv.index("--uid") + 1])
        if "--gid" in "".join(sys.argv)
        else os.getgid()
    )

    pconn, cconn = mp.Pipe()
    config_path = Path("~/.config/dfctl/config.json").expanduser()
    CONFIG = Config(config_path, uid, gid, pconn)
    mp.Process(
        target=CONFIG.gitter.return_run(),
        args=(cconn, uid, gid, CONFIG["dots_path"]),
    ).start()

    pconn.recv()
    try:
        cli(CONFIG)
    finally:
        CONFIG.gitter.exit()


if __name__ == "__main__":
    main()
