import tempfile


try:
    from tempfile import TemporaryDirectory

except ImportError:
    import shutil

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
            pass

        @property
        def name(self):
            return self.__temp_dir

        def cleanup(self):
            shutil.rmtree(self.name)
