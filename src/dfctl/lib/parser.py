import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from git import Remote, Repo
from rich.console import Console
from rich.prompt import Confirm

from dfctl.lib.config import Config
from dfctl.lib.git import pull, push
from dfctl.lib.target import TargetExtentions, get_target_groups


@dataclass()
class SubParserSetupReturn:
    mode: None | TargetExtentions = None
    autopullsh: bool = False
    invert_notfind: bool = False
    ask: str = "Are you sure you want to proceed"
    ask_end: str = "?"


class SubParser(ABC):
    @abstractmethod
    def func(self, args: argparse.Namespace, config: Config):
        pass

    @abstractmethod
    def setup(self, subparser: argparse.ArgumentParser) -> SubParserSetupReturn:
        pass

    class FuncDeco:
        def __init__(self, config: Config, setup: SubParserSetupReturn) -> None:
            self.config = config
            self.setup = setup
            self.console = Console()
            self._args: argparse.Namespace

        def __enter__(self):
            try:
                if not self.setup.mode:
                    if self._args.mode:
                        self.setup.mode = TargetExtentions[self._args.mode.upper()]
                    else:
                        raise ValueError("specify the mode")
                groups = get_target_groups(
                    self._args.target,
                    Path(self.config["dots_path"]).expanduser(),
                    self.setup.mode,
                    self.setup.invert_notfind,
                )

                self.console.log(
                    f"[bold blue]Selected[/] {[f"{str(x)}" for x in groups]}"
                )

                if (
                    Confirm.ask(f"{self.setup.ask}{self.setup.ask_end}")
                    if not self._args.noconfirm
                    else True
                ):
                    return groups
            except Exception:
                pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __call__(self, func):
            def __deco(*args, **kwargs):
                self._args = args[0]

                if args[0].autopull and self.setup.autopullsh:
                    pull(self.config.remote)

                with self as groups:
                    result: None | Callable = None
                    self._args.groups = groups
                    new_args = (self._args, self.config)
                    result = func(*new_args, **kwargs)

                if args[0].autopush and self.setup.autopullsh:
                    push(self.config.remote)

                return result

            return __deco

    def __init__(self, subparser: argparse.ArgumentParser, config: Config):
        setup: SubParserSetupReturn = self.setup(subparser)
        subparser.set_defaults(func=self.FuncDeco(config, setup)(self.func))
