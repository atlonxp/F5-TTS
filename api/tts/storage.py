import os
import re
import uuid

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from django.utils.text import slugify


class CustomPublicFileSystemStorage(FileSystemStorage):
    """
    File system storage that saves its files in the filer public directory

    See ``filer.settings`` for the defaults for ``location`` and ``base_url``.
    """
    is_secure = False


def get_valid_filename_django(name):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)
    return s


def get_valid_filename(s):
    """
    like the regular get_valid_filename, but also slugifies away
    umlauts and stuff.
    """
    s = get_valid_filename_django(s)
    filename, ext = os.path.splitext(s)
    filename = f"{uuid.uuid4().hex}"
    ext = slugify(ext)
    print('filename', filename)
    print('ext', ext)
    if ext:
        return "{}.{}".format(filename, ext)
    else:
        return "{}".format(filename)


def randomized(instance, filename):
    uuid_str = str(uuid.uuid4())
    return os.path.join(uuid_str[0:2], uuid_str[2:4], uuid_str, get_valid_filename(filename))
