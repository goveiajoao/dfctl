from pathlib import Path

from rich.console import Console

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup, mk_instance_target


class CMD(SubParser):
    def func(self, args, config):
        console = Console()
        groups: list[TargetGroup] = args.groups
        if len(groups) > 1:
            raise ValueError("just one intarget for mk")

        group = groups[0]
        mk_instance_target(group, Path(args.path).expanduser())

        config.gitter.commit(f"Created '{str(group)}'")
        console.log(f"Created '{str(group)}'")

    def setup(self, subparser):
        subparser.add_argument(
            "target",
            help="""
            the instance to make (instances start at 0);
            E.G: "User@tmux:main/0" or just "tmux" """,
        )

        subparser.add_argument(
            "path",
            help="""
            the path where the instance links (folder or file);
            E.G: "~/.config/tmux" """,
        )

        return SubParserSetupReturn(TargetExtentions.INSTANCE, True, False)
