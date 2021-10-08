import os
import stat
import shutil
import random
import logging

logger = logging.getLogger(__name__)



def human_size(num, suffix="B"):
    """
    Convert bytes length to a human-readable version
    """
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return "{0:3.1f}{1!s}{2!s}".format(num, unit, suffix)
        num /= 1024.0
    return "{0:.1f}{1!s}{2!s}".format(num, "Yi", suffix)


def copytree(src, dst, metadata=True, symlinks=False, ignore=None):
    """
    This is a contributed re-implementation of 'copytree' that
    should work with the exact same behavior on multiple platforms.
    When `metadata` is False, file metadata such as permissions and modification
    times are not copied.
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


def unique_id(length=12, has_numbers=True):
    sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sequence += sequence.lower()
    if has_numbers:
        sequence += "0123456789"
    return "".join(random.sample(sequence, length))
