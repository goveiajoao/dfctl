from typing import Any, Callable
from pathlib import Path

def take_value(request:bool, on_true:Any=True, on_false:Any=False):
    if request: return on_true() if isinstance(on_true,Callable) else on_true
    else:       return on_false() if isinstance(on_false,Callable) else on_false
def beautypath(path:Path) -> Path:
    home = path.home()
    result = path
    try:
        result = Path('~') / path.relative_to(home)
    except ValueError:
        pass
    return result
