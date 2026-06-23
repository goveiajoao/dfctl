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

                raw_deps = group.get_deps()
                deps_result, deps_by_key, deps_by_values = group.check_deps()
                if len(raw_deps) > 0:
                    nm_deps = nm_group.add(
                        f"{'[bold green]' if deps_result else '[bold red]'}deps"
                    )
                    for k, v in raw_deps.items():
                        nm_deps_check = nm_deps.add(
                            f"{'[bold green]' if deps_by_key[k] else '[bold red]'}{k}"
                        )
                        for _, i in enumerate(v):
                            nm_deps_check.add(
                                f"{'[bold green]' if deps_by_values[k][_] else '[bold red]'}{i}"
                            )

                nm_syms = nm_group.add("[bold purple]syms")
                syms = group.get_syms()
                for k, v in syms.items():
                    nm_syms.add(f"([blue]{k}[/] > [blue]{v}[/])")

                nm_branchs = nm_group.add("[purple]branchs")
                for branch in next(group.path.walk())[1]:
                    status = "[bold red]"
                    branch_content = [
                        y for x in next((group.path / branch).walk())[1:] for y in x
                    ]
                    try:
                        status = (
                            "[bold green]"
                            if installed_groups[group.name].branch == branch
                            else status
                        )
                    except Exception:
                        pass
                    nm_branchs.add(
                        f"{status}{branch}[/] - [{','.join(f"[bold blue]{x}[/]" for x in branch_content)}]"
                    )
            console.log(tree)

    def setup(self, subparser):
        return SubParserSetupReturn(None)

    def generate(self, subparsers, name, parents):
        return subparsers.add_parser(name, parents=parents, help="lists the dotfile")
