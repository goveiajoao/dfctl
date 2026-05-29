import argparse
import os
import sys
from pathlib import Path

import dfctl.cli.cmd as cmd
from dfctl.lib.config import Config


def main():

    # Sudo Error
    if os.getuid() == 0 and "--sudoreload" not in sys.argv:
        raise Exception("please do not run as root")

    # Config
    #   NOTE: adapted for sudo loop, thats why its ugly af
    config_path: Path
    if "-c" in sys.argv:
        config_path = Path(sys.argv[sys.argv.index("-c") + 1])
    else:
        config_path = Path("~/.config/dfctl/config.json").expanduser()
        sys.argv.append("-c")
        sys.argv.append(str(config_path))

    CONFIG: Config = Config(config_path)
    if "-d" in sys.argv:
        CONFIG.dots_path = Path(sys.argv[sys.argv.index("-d") + 1])
    else:
        sys.argv.append("-d")
        sys.argv.append(str(CONFIG["dots_path"]))
    CONFIG.takegit()

    # Parser Section
    arguments_parser = argparse.ArgumentParser(add_help=False)
    arguments_parser.add_argument(
        "-c",
        help="config file (~/.config/dfctl/config.json)",
    )
    arguments_parser.add_argument(
        "-d",
        help="dots path (~/.dotfiles/)",
    )
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
        "--sudoreload",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
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
    args.func(args)


if __name__ == "__main__":
    main()
