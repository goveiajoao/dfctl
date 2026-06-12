import json
from collections import defaultdict
from pathlib import Path

from rich import print
from rich.console import Console
from rich.tree import Tree

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetGroup, get_available_groups, get_installed_branchs


class CMD(SubParser):
    def func(self, args, config):
        console = Console(style="bold")
        dots_path: Path = config["dots_path"]
        groups: list[TargetGroup] = get_available_groups(dots_path)
        installed_branchs: list[TargetGroup] = get_installed_branchs(dots_path)

        installed_groups: dict[str, TargetGroup] = {}
        for branch in installed_branchs:
            installed_groups[branch.name] = branch

        levelsg: defaultdict[str, list[TargetGroup]] = defaultdict(list)
        for group in groups:
            levelsg[group.level].append(group)

        for k, v in levelsg.items():
            tree = Tree(f"[bold blue]{k}")
            for group in v:
                nm_group = tree.add(
                    f"{"[bold green]" if group.name in installed_groups else "[bold red]"}{group.name}"
                )
                nm_syms = nm_group.add("[bold purple]syms")
                syms = group.get_syms()
                for k, v in syms.items():
                    nm_syms.add(f"([blue]{k}[/] > [blue]{v}[/])")

                for branch in next(group.path.walk())[1]:
                    status = "[bold red]"
                    try:
                        status = (
                            "[bold green]"
                            if installed_groups[group.name].branch == branch
                            else status
                        )
                    except Exception:
                        pass
                    nm_group.add(f"{status}{branch}")
            console.log(tree)

    def setup(self, subparser):
        return SubParserSetupReturn(None)
