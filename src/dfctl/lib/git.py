from pathlib import Path

from git import InvalidGitRepositoryError, Remote, Repo
from rich.console import Console

from dfctl.lib.elevate import go_to_user


def pull(remove: Remote):
    console = Console()
    with console.status("[bold green]Pulling from repo..."):
        remove.pull()


def push(remove: Remote):
    console = Console()
    with console.status("[bold green]Pushing to repo..."):
        remove.push()


def take_repo(path: Path):
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        raise InvalidGitRepositoryError(f"Git repo dont exists in '{path}'")


def take_remote(repo: Repo):
    try:
        return repo.remote()
    except Exception:
        raise ValueError("Please create 'origin' remote in the repo")


def add_commit(repo: Repo, msg: str = ""):
    repo.git.add(all=True)
    repo.index.commit(msg)


def gitter_run(cconn, uid: int, gid: int, dots_path):
    go_to_user(uid, gid)
    try:
        repo = take_repo(dots_path)
        remote = take_remote(repo)
    finally:
        cconn.send("ready")
    try:
        while True:
            try:
                msg = cconn.recv().split(" ")
                match msg[0]:
                    case "test":
                        print("TEST!")
                    case "pull":
                        pull(remote)
                    case "push":
                        push(remote)
                    case "commit":
                        add_commit(repo, " ".join(msg[1:]))
                    case "exit":
                        break

                cconn.send("done")

            except EOFError:
                break
    finally:
        print("CLOSSED")
        cconn.close()


class Gitter:
    def __init__(self, pconn) -> None:
        self.pconn = pconn

    def return_run(self):
        return gitter_run

    def dowait(self):
        self.pconn.recv()

    def test(self):
        self.pconn.send("test")
        self.dowait()

    def pull(self):
        self.pconn.send("pull")
        self.dowait()

    def push(self):
        self.pconn.send("push")
        self.dowait()

    def commit(self, msg: str = ""):
        self.pconn.send(f"commit {msg}")
        self.dowait()

    def exit(self):
        self.pconn.send("exit")
