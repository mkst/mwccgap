from pathlib import Path
import re


class MakeRule:
    target: str
    source: str | None
    includes: list[str]

    def __init__(self, data: bytes, use_wibo=False):
        if use_wibo:
            encoding = "iso-8859-1"
        else:
            encoding = "utf-8"

        rule = data.decode(encoding)
        rule = re.sub(r"\\[\r\n]+", " ", rule)
        (target, remaining) = re.split(": ", rule)
        files = remaining.split()
        files.insert(0, target)

        if use_wibo:
            files = [path_from_wibo(p) for p in files]

        # the first file is the target, the second is the
        self.target = files.pop(0)
        self.source = files.pop(0)
        self.includes = files

    def as_str(self):
        rule = f"{self.target}: "
        if self.source is not None:
            rule += f"{self.source} "
        for file in self.includes:
            rule += f"\\\n\t{file} "
        rule += "\n"

        return rule


# an implementation of the wibo translation from "windows"
# path to a unix path
def path_from_wibo(path_str: str) -> Path:
    path_str = path_str.replace("\\", "/")

    # remove the extended path prefix
    if path_str.startswith("//?/"):
        path_str = path_str[4:]

    # remove the drive letter
    if path_str.lower().startswith("z:/"):
        path_str = path_str[2:]

    # if it exists, we're done
    path = Path(path_str)
    if path.is_file():
        return path

    # otherwise try to find a case insensitive match
    new_path = Path(".")
    for part in path.parts:
        candidate = new_path / part
        if new_path.is_dir():
            for entry in new_path.iterdir():
                if entry.name.lower() == part.lower():
                    candidate = new_path / entry.name
                    break
        new_path = candidate

    return new_path
