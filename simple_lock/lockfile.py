"""
This program is based on `pylockfile`.

"""
import os
import time
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

        self.lockfile = self.path / self.name

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
        return "<%s: %r -- %r>" % (self.__class__.__name__, self.lockfile,
                                   self.path)

    
class SimpleLock(LockBase):
    "Demonstrate file-based locking."
    root_path = '.'
    
    def __init__(self, name='lockfile.lock', path='.', threaded=True):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        if path == '.':
            path = self.root_path
        super().__init__(name, path, threaded)

    @classmethod
    def set_root_path(cls, path):
        _p = Path(path).expanduser().resolve()
        if not _p.exists():
            raise ValueError('{} directory does not exist.'.format(_p))
        cls.root_path = str(_p)

    @classmethod
    def watch(cls, name, path='.'):
        if path == '.':
            path = cls.root_path
        path = Path(path).expanduser().resolve()
        _file = path / name
        return _file.exists()
        
    def acquire(self):
        if self.is_locked():
            return False
        try:
            _fp = self.lockfile.open("w")
            _fp.write('{}\n{}\n'.format(self.hostname, self.pid))
            _fp.close()
        except IOError:
            raise LockFailed("failed to create %s" % self.lockfile)
        return True

    def release(self):
        if not self.is_locked():
            raise NotLocked("%s is not locked" % self.lockfile)
        elif not os.path.exists(self.lockfile):
            raise NotMyLock("%s is locked, but not by me" % self.lockfile)
        self.lockfile.unlink()

    def is_locked(self):
        return self.lockfile.exists()

    def i_am_locking(self):
        return (self.is_locked() and
                self.lockfile.exists() and
                self.lockfile.stat().st_nlink == 2)

    def break_lock(self):
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

def lock(name='lockfile.lock', path='.',
         threaded=True, func=None, *dargs, **dkwargs):
    def decorate(func):
        def wrapper(*args, **kwargs):
            lockfile = SimpleLock(name=name,
                                  path=path,
                                  threaded=threaded)
            acquired_flag = lockfile.acquire()
            try:
                rtn = func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                if acquired_flag:
                    lockfile.release()
            return rtn
        return wrapper
    return decorate

def watch(func, name='lockfile.lock', path='.',
                   code=None, error_type=None,
                   status_code=None, message=None):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if SimpleLock.watch(name=name, path=path):        
            the_response = Response()
            the_response.code = code
            the_response.error_type = error_type
            the_response.status_code = status_code
            the_response._content = b'f{message}'
            return the_response
        return func(*args, **kwargs)
    return wrapper
