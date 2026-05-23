from abc import ABC, abstractmethod
import argparse

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
