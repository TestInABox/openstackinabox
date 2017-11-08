"""
Py2 TemporaryDirectory support
"""
import shutil
import tempfile


class TemporaryDirectory(object):

    def __init__(self, suffix='', prefix='tmp', dir=None):
        self.__temp_dir = tempfile.mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def __repr__(self):
        return 'TemporaryDirectory({0})'.format(self.name)

    @property
    def name(self):
        return self.__temp_dir

    def cleanup(self):
        try:
            shutil.rmtree(self.name)
        except OSError:
            pass
