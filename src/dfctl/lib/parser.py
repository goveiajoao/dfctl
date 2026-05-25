from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass, field
from rich.console import Console
from rich.prompt import Confirm
from dfctl.lib.target import TargetGroup


class SubParser(ABC):
    @abstractmethod
    def func(self, args:argparse.Namespace):
        pass
    @abstractmethod
    def setup(self, subparser:argparse.ArgumentParser):
        pass

    def __init__(self, subparser:argparse.ArgumentParser):
        self.setup(subparser)
        subparser.set_defaults(func=self.func)
