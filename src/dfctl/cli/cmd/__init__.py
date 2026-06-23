import argparse
import importlib
import pkgutil

from rich.console import Console

import dfctl.cli.cmd as cmd_iter
from dfctl.lib.config import Config


def init(
    subparsers: argparse._SubParsersAction,
    config: Config,
    argument_parser: argparse.ArgumentParser,
):
    console = Console(stderr=True, style="bold red")
    for _, name, _ in pkgutil.iter_modules(cmd_iter.__path__):
        full_name = f"{cmd_iter.__name__}.{name}"
        module = importlib.import_module(full_name)
        try:
            module.CMD(
                subparsers,
                name,
                [argument_parser],
                config,
            )
        except Exception as e:
            console.log(e)
