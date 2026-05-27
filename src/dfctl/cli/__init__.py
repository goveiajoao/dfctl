import argparse
from pathlib import Path

import dfctl.cli.cmd as cmd
from dfctl.lib.config import Config

#
# class pull(SubParser):
#     def func(self, args):
#         with console.status("[bold green]Pulling from repo..."):
#             REPO_REMOTE.pull()
#
#     def setup(self, subparser):
#         pass
#
#
# class push(SubParser):
#     def func(self, args):
#         REPO.git.add(all=True)
#         REPO.index.commit("Update")
#         with console.status("[bold green]Pushing to repo..."):
#             REPO_REMOTE.push()
#
#     def setup(self, subparser):
#         pass


def main():
    CONFIG: Config = Config(Path("~/.config/dfctl/config.json").expanduser())
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="dfctl",
        description="Dotfiles CLI",
        color=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    parser.add_argument(
        "--noconfirm",
        action="store_true",
        help=f"skip confirmation prompts                ({CONFIG["noconfirm"]})",
    )
    parser.add_argument(
        "--autopull",
        action="store_false",
        help=f"auto pull before any local-repo action   ({CONFIG["autopull"]})",
    )
    parser.add_argument(
        "--autopush",
        action="store_false",
        help=f"auto push after any local-repo action    ({CONFIG["autopush"]})",
    )
    subparsers: argparse._SubParsersAction = parser.add_subparsers(required=True)

    #
    #   <CMDs>
    #
    cmd.init(subparsers, CONFIG)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
