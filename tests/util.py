import os


def get_resource_filename(filename, *, ext=None):
    if ext and not filename.endswith(ext):
        filename += ext
    testdir = os.path.dirname(__file__)
    return os.path.join(testdir, "resources", filename)


def open_resource(filename, *, mode="r", encoding="utf-8", **kwargs):
    filename = get_resource_filename(filename, **kwargs)
    return open(filename, mode=mode, encoding=encoding)


def load_resource(filename, **kwargs):
    with open_resource(filename, **kwargs) as fp:
        return fp.read()
