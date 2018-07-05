"""
This program is based on `pylockfile`.

"""
import os
import socket
import typing
import functools
import threading
import contextlib
import subprocess
from pathlib import Path


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
    delimiter = '_-_-_'
    def __init__(self, name, path, threaded=True, delimiter='_-_-_'):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        super(LockBase, self).__init__(path)
        self.name = name        
        self.path = Path(path).expanduser().resolve()        
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self.delimiter = delimiter
        if threaded:
            t = threading.current_thread()
            # Thread objects in Python 2.4 and earlier do not have ident
            # attrs.  Worm around that.
            ident = getattr(t, "ident", hash(t))
            self.tname = "-%x" % (ident & 0xffffffff)
        else:
            self.tname = ""

        _foramt = '{name}{delimiter}{hostname}{delimiter}{pid}'
        self.lockfile = self.path / (_foramt.format(name=self.name,
                                                    delimiter=self.delimiter,
                                                    hostname=self.hostname,
                                                    pid=self.pid))

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
    
    def __init__(self, filename='simple.lock', path='.', threaded=True):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        if path == '.':
            path = self.root_path
        super().__init__(filename, path, threaded)

    @classmethod
    def set_root_path(cls, path):
        _p = Path(path).expanduser()
        if not _p.exists():
            raise ValueError('{} directory does not exist.'.format(_p))
        _p = _p.resolve()
        cls.root_path = str(_p)

    @classmethod
    def watch(cls, filename, path='.'):
        cls.clean(filename, path)
        if path == '.':
            path = cls.root_path
        path = Path(path).expanduser().resolve()
        _files = list(path.glob(filename + "*"))
        return bool(_files)

    @classmethod
    def clean(cls, filename, path='.'):
        if path == '.':
            path = cls.root_path
        path = Path(path).expanduser().resolve()
        hostname = socket.gethostname()
        for ifile in path.glob(filename + cls.delimiter + "*"):
            _hostname = ifile.name.split(cls.delimiter)[1]
            pid = ifile.name.split(cls.delimiter)[2]
            if hostname == _hostname:
                p = subprocess.run(["ps -ero pid"], stdout=subprocess.PIPE,
                                    shell=True, check=True, universal_newlines=True)
                if not pid in p.stdout.split():
                    ifile.unlink()
        
    def acquire(self):
        self.clean(self.name, self.path)
        if self.is_locked():
            return False
        try:
            with self.lockfile.open("w"): pass
        except IOError:
            raise LockFailed("failed to create %s" % self.lockfile)
        return True

    def release(self):
        if not self.is_locked():
            raise NotLocked("%s is not locked" % self.lockfile)
        elif not os.path.exists(str(self.lockfile)):
            raise NotMyLock("%s is locked, but not by me" % self.lockfile)
        self.lockfile.unlink()

    def is_locked(self):
        path = Path(self.lockfile).parent
        _files = list(path.glob(str(self.name) + self.delimiter + "*"))
        return bool(_files)

    def i_am_locking(self):
        return (self.is_locked() and
                self.lockfile.exists() and
                self.lockfile.stat().st_nlink == 2)

    def break_lock(self):
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

def lock(filename='simple.lock',
         path='.',
         threaded=True,
         return_value: typing.Callable = None,
         **return_func_kwargs):
    def decorate(func):
        @functools.wraps(func)        
        def wrapper(*args, **kwargs):
            lockfile = SimpleLock(filename=filename,
                                  path=path,
                                  threaded=threaded)
            acquired_flag = lockfile.acquire()
            try:
                if acquired_flag:
                    rtn = func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                if acquired_flag:
                    lockfile.release()
                else:
                    if return_value is not None:
                        if callable(return_value):
                            return return_value(**return_func_kwargs)
                        else:
                            return return_value
                    else:
                        rtn = None
            return rtn
        return wrapper
    return decorate

def watch(filename='simple.lock',
          path='.',
          threaded=True,
          return_value: typing.Callable = None,
          **return_func_kwargs):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if SimpleLock.watch(filename=filename, path=path):
                if return_value is not None:
                    if callable(return_value):
                        return return_value(**return_func_kwargs)
                    else:
                        return return_value
                return False
            return func(*args, **kwargs)
        return wrapper
    return decorate

