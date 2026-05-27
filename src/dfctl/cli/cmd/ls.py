from collections import defaultdict
from pathlib import Path

from rich import print
from rich.tree import Tree

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetGroup, get_available_groups, get_installed_branchs


class CMD(SubParser):
    def func(self, args, config):
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
            tree = Tree(k)
            for group in v:
                nm_group = tree.add(
                    f"{'*' if group.name in installed_groups else ''}{group.name}"
                )
                for branch in next(group.path.walk())[1]:
                    status = ""
                    try:
                        status = (
                            "*"
                            if installed_groups[group.name].branch == branch
                            else status
                        )
                    except Exception:
                        pass

                    nm_branch = nm_group.add(f"{status}{branch}")
                    instances = [
                        y for x in next((group.path / branch).walk())[1:] for y in x
                    ]
                    for instance in instances:
                        if instance not in ["syms.json"]:
                            nm_branch.add(instance)
            print(tree)

    def setup(self, subparser):
        return SubParserSetupReturn(None)
