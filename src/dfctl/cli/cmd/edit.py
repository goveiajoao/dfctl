import os
from collections import defaultdict
from pathlib import Path

from rich import print
from rich.console import Console
from rich.tree import Tree

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup, get_available_groups


class CMD(SubParser):
    def func(self, args, config):
        groups: list[TargetGroup] = args.groups
        for group in groups:
            os.system(f"{config['editor']} {str(group.path)}")
            config.gitter.commit(f"edit on '{str(group)}'")

    def setup(self, subparser):
        subparser.add_argument("target", help="instance target")
        return SubParserSetupReturn(TargetExtentions.INSTANCE, (True, True), True, None)
