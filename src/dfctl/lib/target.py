import json
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class WholeNumber(int):

    def __new__(cls, value: int | str = 0):
        if not isinstance(value, int):
            value = int(value)
        if value < 0:
            raise ValueError("Value must be >= 0")
        return super().__new__(cls, value)


class TargetExtentions(Enum):
    # NAME = [Symbol,Default]
    LEVEL = ("@", "user")
    GROUP = None
    BRANCH = (":", "main")
    INSTANCE = ("/", WholeNumber(0))


@dataclass
class TargetGroup:
    name: str
    level: str
    branch: str
    instance: WholeNumber
    range: TargetExtentions
    path: Path

    def __str__(self):
        extentions: dict[str, tuple] = {
            x.name: x.value for x in TargetExtentions if x.value
        }
        symbols: list[str] = [v[0] for v in extentions.values()]
        match self.range:
            case TargetExtentions.LEVEL:
                return f"{self.level}{symbols[0]}"
            case TargetExtentions.GROUP:
                return f"{self.level}{symbols[0]}{self.name}"
            case TargetExtentions.BRANCH:
                return f"{self.level}{symbols[0]}{self.name}{symbols[1]}{self.branch}"
            case TargetExtentions.INSTANCE:
                return f"{self.level}{symbols[0]}{self.name}{symbols[1]}{self.branch}{symbols[2]}{self.instance}"

    def __post_init__(self):
        extentions: dict[str, tuple] = {
            x.name: x.value for x in TargetExtentions if x.value
        }
        symbols: list[str] = [v[0] for v in extentions.values()]

        string = str(self)
        for x in symbols:
            string = string.replace(x, "/")
        self.path = self.path / string


def sudo_level_in_argv(argv: list, sudo_levels=["system"]):
    for level in sudo_levels:
        if f"{level}{TargetExtentions.LEVEL.value[0]}" in "".join(argv):
            return True
    return False


def get_target_groups(
    raw: str,
    path: Path,
    range: TargetExtentions,
    invert_notfound: bool = False,
):

    raw_list: str = raw[raw.find("[") : raw.rfind("]") + 1]
    raw_nolist: str = raw.replace(raw_list, "")
    available_levels: list = [x for x in next(path.walk())[1] if x[0] != "."]
    available_levelsg: dict = {
        level: next((path / level).walk())[1] for level in available_levels
    }

    extentions: dict[str, tuple] = {
        x.name: x.value for x in TargetExtentions if x.value
    }
    names: list[str] = [k for k in extentions.keys()]
    range_ind: int = (
        next(_ for _, x in enumerate(names) if x == range.name)
        if range.name != "GROUP"
        else 0
    )
    excludes_names: list[str] = [k for k in names[range_ind + 1 :]]
    symbols: list[str] = [v[0] for v in extentions.values()]
    defaults: list[Any] = [v[1] for v in extentions.values()]

    for _, name in enumerate(names):
        symbol = symbols[_]
        default = defaults[_]
        match raw_nolist.count(symbol):
            case 0:
                match name:
                    case TargetExtentions.LEVEL.name:
                        raw = f"{default}{symbol}{raw}"
                    case TargetExtentions.BRANCH.name:
                        raw = f"{raw}{symbol}{default}"
                        if raw.count(symbols[_ + 1]) != 0:
                            raw = f"{raw[:raw.find(symbols[_+1])]}{symbol}{default}{raw[raw.find(symbols[_+1]):]}"
                    case TargetExtentions.INSTANCE.name:
                        raw = f"{raw}{symbol}{default}"
            case 1:
                if name in excludes_names:
                    raise ValueError(f"{name} cannot be passed in range {range.name}")
            case _:
                raise ValueError(f"{name} passed more than once")

    input_level: str = raw[: raw.find(symbols[0])]
    levels: list = [input_level] if input_level != "*" else available_levels
    if input_level not in available_levels and input_level != "*":
        raise ValueError(
            f"level '{input_level}' does not exist, available ones: {available_levels}"
        )
    if symbols[0] in raw_list:
        raise ValueError("set the level outside the list")

    groups: None | list = (
        raw_list[1 : len(raw_list) - 1].replace(" ", "").split(",")
        if raw_list
        else [raw[raw.find(symbols[0]) + 1 : raw.rfind(symbols[1])]]
    )
    if "*" in groups:
        if groups[0] != "*":
            raise ValueError("please use * inside lists as first element")
        groups = groups[1:] + [
            x for k, v in available_levelsg.items() for x in v if k in levels
        ]

    general_branch: str = raw[raw.rfind(symbols[1]) + 1 : raw.rfind(symbols[2])]
    general_instance: str = raw[raw.rfind(symbols[2]) + 1 :]

    result: list[TargetGroup] = []
    result_remove_list: list[str] = []
    for group in groups:
        level: str = input_level
        name: str = group[
            : [
                group.find(symbols[ind]) if group.count(symbols[ind]) else len(group)
                for ind in [1, 2]
            ][0]
        ]
        mode: Literal["add", "remove"] = "add" if name[0] != "-" else "remove"
        name = name[1:] if name[0] == "-" else name

        try:
            level = next(
                k
                for k, v in {
                    k: v for k, v in available_levelsg.items() if k in levels
                }.items()
                if name in v
            )
        except Exception:
            if not invert_notfound:
                raise ValueError(f"group '{name}' does not exist in levels {levels}")

        branch: str = (
            group[
                group.find(symbols[1]) + 1 if group.count(symbols[1]) else 0 : (
                    group.find(symbols[2]) if group.count(symbols[2]) else len(group)
                )
            ]
            if group.count(symbols[1])
            else general_branch
        )
        if not invert_notfound and branch not in next((path / level / name).walk())[1]:
            raise ValueError(
                f"branch '{branch}' does not exist in group '{level}{symbols[0]}{name}'"
            )

        instance: WholeNumber = (
            WholeNumber(group[group.find(symbols[2]) + 1 :])
            if group.count(symbols[2])
            else WholeNumber(general_instance)
        )
        if not invert_notfound and str(instance) not in [
            y for x in next((path / level / name / branch).walk())[1:] for y in x
        ]:
            raise ValueError(
                f"instance '{instance}' does not exist in branch '{level}{symbols[0]}{name}{symbols[1]}{branch}'"
            )

        match mode:
            case "add":
                result.append(TargetGroup(name, level, branch, instance, range, path))
            case "remove":
                result_remove_list.append(name)

    result = [x for x in result if x.name not in result_remove_list]
    return result


def get_available_groups(path: Path) -> list[TargetGroup]:
    return get_target_groups("*@*", path, TargetExtentions.GROUP)


def get_available_branchs(path: Path) -> list[TargetGroup]:
    available_groups = get_available_groups(path)
    return [
        TargetGroup(x.name, x.level, y, x.instance, TargetExtentions.BRANCH, path)
        for x in available_groups
        for y in next(x.path.walk())[1]
    ]


def get_deps(
    target: TargetGroup,
) -> dict:
    if target.range.name in [TargetExtentions.GROUP.name, TargetExtentions.BRANCH.name]:
        with open(target.path / ".deps.json", "r") as File:
            return json.load(File)
    else:
        raise Exception("invalid target range")


def check_deps(
    target: TargetGroup,
) -> bool:
    deps = get_deps(target)

    for k, v in deps.items():
        if not isinstance(v, list):
            raise Exception(f"deps not right in {str(target)}")
        match k:
            case "which":
                for x in v:
                    if shutil.which(x) is None:
                        return False
            case "exists":
                for x in v:
                    if not Path(x).expanduser().exists():
                        return False

    return True


def get_syms(
    target: TargetGroup,
) -> dict:
    if target.range.name == TargetExtentions.GROUP.name:
        with open(target.path / ".syms.json", "r") as File:
            return json.load(File)
    else:
        raise Exception("invalid target range")


def add_syms(target: TargetGroup, sym: Path) -> int:
    if target.range.name == TargetExtentions.BRANCH.name:

        syms = get_syms(target)
        new_index = syms[::-1][0]
        syms[new_index] = sym

        with open(target.path / ".syms.json", "w") as File:
            json.dump(syms, File)

        return new_index

    else:
        raise Exception("invalid target range")


def get_installed_branchs(path: Path) -> list[TargetGroup]:
    available_branchs = get_available_branchs(path)
    installed_branchs: list = []
    for group in available_branchs:
        with open(group.path / "syms.json", "r") as File:
            syms: dict = json.load(File)

        for original, sym in syms.items():
            original = Path().joinpath(group.path, original)
            sym = Path(sym).expanduser()

            if sym.exists() and sym.is_symlink() and sym.readlink() == original:
                installed_branchs.append(group)
                break
    return installed_branchs
