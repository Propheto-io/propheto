import os
import stat
import shutil
import random
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def human_size(num: float, suffix: Optional[str] = "B"):
    """
    Convert bytes length to a human-readable version.

    Parameters
    ----------
    num : float
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return "{0:3.1f}{1!s}{2!s}".format(num, unit, suffix)
        num /= 1024.0
    return "{0:.1f}{1!s}{2!s}".format(num, "Yi", suffix)


def copytree(
    src: str,
    dst: str,
    metadata: Optional[bool] = True,
    symlinks: Optional[bool] = False,
    ignore=None,
) -> None:
    """
    This is a contributed re-implementation of 'copytree' that
    should work with the exact same behavior on multiple platforms.
    When `metadata` is False, file metadata such as permissions and modification
    times are not copied.

    Parameters
    ----------
    src: str,
    dst: str,
    metadata: Optional[bool] = True,
    symlinks: Optional[bool] = False,
    ignore=None
    

    """

    def copy_file(src, dst, item):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)

        if symlinks and os.path.islink(s):  # pragma: no cover
            if os.path.lexists(d):
                os.remove(d)
            os.symlink(os.readlink(s), d)
            if metadata:
                try:
                    st = os.lstat(s)
                    mode = stat.S_IMODE(st.st_mode)
                    os.lchmod(d, mode)
                except:
                    pass  # lchmod not available
        elif os.path.isdir(s):
            copytree(s, d, metadata, symlinks, ignore)
        else:
            shutil.copy2(s, d) if metadata else shutil.copy(s, d)

    try:
        lst = os.listdir(src)
        if not os.path.exists(dst):
            os.makedirs(dst)
            if metadata:
                shutil.copystat(src, dst)
    except NotADirectoryError:  # egg-link files
        copy_file(os.path.dirname(src), os.path.dirname(dst), os.path.basename(src))
        return

    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]

    for item in lst:
        copy_file(src, dst, item)


def unique_id(length=12, has_numbers=True) -> str:
    """
    Generate a unique id

    Parameters
    ----------
    length : int
            The length for the unique identifier.
    has_numbers : bool
            Whether the id should include numbers as well as strings

    Returns
    -------
    uid : str
    """
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sequence += sequence.lower()
    if has_numbers:
        sequence += "0123456789"
    uid = "".join(random.sample(sequence, length))
    return uid


def get_list_directory_files(directory_path: str) -> list:
    """
    Utility function for getting all of the files and paths in a given directory.

    Parameters
    ----------
    directory_path : str
            Path to the directory to search. 
    
    Returns
    -------
    directory_files : list
    """
    directory_contents = os.listdir(directory_path)
    directory_files = []
    for _item in directory_contents:
        _path = Path(directory_path, _item)
        if os.path.isdir(_path):
            subdirectory_files = get_list_directory_files(_path)
            directory_files.extend(subdirectory_files)
        else:
            # Exclude any cache files
            if str(_path)[-4:] != ".pyc":
                directory_files.append(_path)
    return directory_files
