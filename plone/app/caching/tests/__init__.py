import os
import time


class TZEnvContext:
    def __init__(self, tzval):
        self.tzval = tzval
        self._old_tz = None

    def get_current_tz(self):
        return os.environ.get("TZ", None)

    def set_current_tz(self, tzval):
        if tzval is None and "TZ" in os.environ:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = tzval

        time.tzset()

    def __enter__(self):
        self._old_tz = self.get_current_tz()
        self.set_current_tz(self.tzval)

    def __exit__(self, type, value, traceback):
        if self._old_tz is not None:
            self.set_current_tz(self._old_tz)

        self._old_tz = None
