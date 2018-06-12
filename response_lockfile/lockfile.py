"""
This program is based on `pylockfile`.

"""
import os
import time
import fcntl
import socket
import functools
import threading
import contextlib
from pathlib import Path

from requests.models import Response


class Error(Exception):
    """
    Base class for other exceptions.

    >>> try:
    ...   raise Error
    ... except Exception:
    ...   pass
    """
    pass


class LockError(Error):
    """
    Base class for error arising from attempts to acquire the lock.

    >>> try:
    ...   raise LockError
    ... except Error:
    ...   pass
    """
    pass


class LockTimeout(LockError):
    """Raised when lock creation fails within a user-defined period of time.

    >>> try:
    ...   raise LockTimeout
    ... except LockError:
    ...   pass
    """
    pass


class AlreadyLocked(LockError):
    """Some other thread/process is locking the file.

    >>> try:
    ...   raise AlreadyLocked
    ... except LockError:
    ...   pass
    """
    pass


class LockFailed(LockError):
    """Lock file creation failed for some other reason.

    >>> try:
    ...   raise LockFailed
    ... except LockError:
    ...   pass
    """
    pass


class UnlockError(Error):
    """
    Base class for errors arising from attempts to release the lock.

    >>> try:
    ...   raise UnlockError
    ... except Error:
    ...   pass
    """
    pass


class NotLocked(UnlockError):
    """Raised when an attempt is made to unlock an unlocked file.

    >>> try:
    ...   raise NotLocked
    ... except UnlockError:
    ...   pass
    """
    pass


class NotMyLock(UnlockError):
    """Raised when an attempt is made to unlock a file someone else locked.

    >>> try:
    ...   raise NotMyLock
    ... except UnlockError:
    ...   pass
    """
    pass


class _SharedBase(object):
    def __init__(self, path):
        self.path = path

    def acquire(self):
        """
        Acquire the lock.
        """
        raise NotImplemented("implement in subclass")

    def release(self):
        """
        Release the lock.

        If the file is not locked, raise NotLocked.
        """
        raise NotImplemented("implement in subclass")

    def __enter__(self):
        """
        Context manager support.
        """
        self.acquire()
        return self

    def __exit__(self, *_exc):
        """
        Context manager support.
        """
        self.release()

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.path)


class LockBase(_SharedBase):
    """Base class for platform-specific lock classes."""
    def __init__(self, name, path, threaded=True):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        super(LockBase, self).__init__(path)
        self.name = name
        self.path = Path(path).expanduser().resolve()
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        if threaded:
            t = threading.current_thread()
            # Thread objects in Python 2.4 and earlier do not have ident
            # attrs.  Worm around that.
            ident = getattr(t, "ident", hash(t))
            self.tname = "-%x" % (ident & 0xffffffff)
        else:
            self.tname = ""

        # unique name is mostly about the current process, but must
        # also contain the path -- otherwise, two adjacent locked
        # files conflict (one file gets locked, creating lock-file and
        # unique file, the other one gets locked, creating lock-file
        # and overwriting the already existing lock-file, then one
        # gets unlocked, deleting both lock-file and unique file,
        # finally the last lock errors out upon releasing.
        self.unique_name = self.path / self.name

    def is_locked(self):
        """
        Tell whether or not the file is locked.
        """
        raise NotImplemented("implement in subclass")

    def i_am_locking(self):
        """
        Return True if this object is locking the file.
        """
        raise NotImplemented("implement in subclass")

    def break_lock(self):
        """
        Remove a lock.  Useful if a locking thread failed to unlock.
        """
        raise NotImplemented("implement in subclass")

    def __repr__(self):
        return "<%s: %r -- %r>" % (self.__class__.__name__, self.unique_name,
                                   self.path)

    
class ResponseLockFile(LockBase):
    "Demonstrate Django-based locking."
    def __init__(self, name='lockfile.lock', path='.', threaded=True):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        super(ResponseLockFile, self).__init__(name, path, threaded)

    def acquire(self):
        if self.unique_name.exists():
            return False
        try:
            _fp = self.unique_name.open("w")
            _fp.write(f'{self.hostname}\n{self.pid}\n')
            _fp.close()
        except IOError:
            raise LockFailed("failed to create %s" % self.unique_name)
        return True

    def release(self):
        if not self.is_locked():
            raise NotLocked("%s is not locked" % self.unique_name)
        elif not os.path.exists(self.unique_name):
            raise NotMyLock("%s is locked, but not by me" % self.unique_name)
        self.unique_name.unlink()

    def is_locked(self):
        return os.path.exists(self.unique_name)

    def i_am_locking(self):
        return (self.is_locked() and
                os.path.exists(self.unique_name) and
                os.stat(self.unique_name).st_nlink == 2)

    def break_lock(self):
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

    def __enter__(self, name='lockfile.lock', path='.',
                  threaded=True, code=None, error_type=None,
                  status_code=None, message=None):
        if not self.acquire():
            the_response = Response()
            the_response.code = code
            the_response.error_type = error_type
            the_response.status_code = status_code
            the_response._content = b'f{message}'
            return the_response
        return self
        
def http_responselock(func, name='lockfile.lock', path='.',
                      threaded=True, code=None, error_type=None,
                      status_code=None, message=None):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        lockfile = ResponseLockFile(name=name,
                                    path=path,
                                    threaded=threaded)
        acquired_flag = lockfile.acquire()
        if not acquired_flag:        
            the_response = Response()
            the_response.code = code
            the_response.error_type = error_type
            the_response.status_code = status_code
            the_response._content = b'f{message}'
            return the_response
        
        rtn = func(*args, **kwargs)
        if acquired_flag:
            lockfile.release()
        return rtn
    return wrapper

with ResponseLockFile():
    print(1)
    @http_responselock
    def test():
        time.sleep(5)
    test()
        
if __name__ == '__main__':
    pass
