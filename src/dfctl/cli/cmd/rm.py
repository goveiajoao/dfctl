from pathlib import Path
from shutil import rmtree

from rich.console import Console
from rich.tree import Tree

from dfctl.lib.parser import SubParser, SubParserSetupReturn
from dfctl.lib.target import TargetExtentions, TargetGroup, rm_syms


class CMD(SubParser):
    def func(self, args, config):
        console = Console()
        groups: list[TargetGroup] = args.groups
        final_func = self.takebymode(
            TargetExtentions[args.mode.upper()], config, console
        )
        with console.status("[bold red] Removing..."):
            for group in groups:
                final_func(group)

    def takebymode(self, mode, config, console):

        def final(func):
            def __deco(*args, **kwargs):
                msg = str(args[0])
                tree = Tree(f"[bold red]Removed[/] [bold blue]'{msg}'")

                func(*args, tree, **kwargs)
                console.log(tree)
                config.gitter.commit(f"Removed '{msg}'")

            return __deco

        @final
        def default(group: TargetGroup, tree: Tree = Tree("")):
            rmtree(group.path)

        @final
        def instance(group: TargetGroup, tree: Tree = Tree("")):
            # remove from .syms file
            rm_syms(group, group.instance)

            # remove from every branch
            group_path = group.path.parent.parent
            for origin, branchs, _ in group_path.walk():
                for branch in branchs:
                    contents = [
                        y
                        for x in next(Path.joinpath(origin, branch).walk())[1:]
                        for y in x
                    ]
                    for content in contents:
                        path = origin / branch / content
                        if content == str(group.instance):

                            # Delete Instance
                            path.unlink() if path.is_file() else rmtree(path)

                            # Delete Branch
                            if len(contents) == 1:
                                rmtree(origin / branch)
                                tree.add(
                                    f"[bold red]Removed[/] [bold blue]Branch '{branch}'"
                                )

                            # Delete Group
                            if len(next(group_path.walk())[1]) == 0:
                                rmtree(group_path)
                                tree.add(
                                    f"[bold red]Removed[/] [bold blue]Group '{group.name}'"
                                )
                break

        match mode:
            case TargetExtentions.INSTANCE:
                return instance
            case _:
                return default

    def setup(self, subparser):
        mode_choices: list = [
            x.name.lower() for x in TargetExtentions if x.name != "LEVEL"
        ]
        subparser.add_argument(
            "mode",
            metavar="mode",
            choices=mode_choices,
            help=f"{{{','.join(mode_choices)}}}",
        )
        subparser.add_argument("target", help="<mode> target")
        return SubParserSetupReturn(None, True)
