from pathlib import Path

from git import InvalidGitRepositoryError, Remote, Repo
from rich.console import Console
from rich.prompt import Confirm


def pull(remove: Remote):
    console = Console()
    with console.status("[bold green]Pulling from repo..."):
        remove.pull()


def push(remove: Remote):
    console = Console()
    with console.status("[bold green]Pushing to repo..."):
        remove.push()


def take_repo(url: str, path: Path):
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        print(f"Git repo dont exists in '{path}'")
        if Confirm.ask(f"Would you like to clone repo {url} to path {path}"):
            return Repo.clone_from(url, path)
        else:
            exit()


def take_remote(repo: Repo):
    try:
        return repo.remote()
    except Exception:
        raise ValueError("Please create 'origin' remote in the repo")


def add_commit(repo: Repo, msg: str = ""):
    repo.git.add(all=True)
    repo.index.commit(msg)
