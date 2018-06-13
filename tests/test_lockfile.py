import time
from pathlib import Path
from concurrent import futures

import pytest

from simple_lock import SimpleLock
from simple_lock import lock
from simple_lock import watch


success_root_pathes = ['/tmp', '~', '.']
@pytest.mark.parametrize('root_path',
                         success_root_pathes)
def test_root_path(root_path):
    SimpleLock.set_root_path(root_path)
    assert SimpleLock.root_path == str(Path(root_path).expanduser().resolve())

fail_root_pathes = ['/hoge/hoge', '/hoge/~/hoge']
@pytest.mark.parametrize('root_path',
                         fail_root_pathes)
def test_root_path_fail_cases(root_path):
    with pytest.raises(ValueError):
        SimpleLock.set_root_path(root_path)

        
def test_check_not_existance_lockfile_when_define_function(tmpdir):
    # GIVEN: direcotry
    # WHEN: a wrapped function is defined
    # THEN: lockfile is not created
    p = tmpdir.mkdir("sub")
    lockfile = p / 'lockfile.lock'
    @lock(filename='lockfile.lock', path=str(p))
    def sleep_func():
        pass
    with pytest.raises(AssertionError):        
        assert lockfile.exists()

def test_check_collectly_create_lockfile(tmpdir):
    # GIVEN: direcotry
    # WHEN: a wrapped function is called
    # THEN: lockfile is created
    p = tmpdir.mkdir("async")
    
    @lock(filename='lockfile.lock', path=str(p))
    def sleep_func():
        time.sleep(0.5)
        return (True, 'sleep')
    def check_lockfile():
        time.sleep(0.2)        
        lockfile = p / 'lockfile.lock'
        return (lockfile.exists(), 'check_lockfile')
    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        funcs = [sleep_func, check_lockfile]
        to_do = [executor.submit(f) for f in funcs]
        done = [f.done() for f in futures.as_completed(to_do)]
        while True:
            if all(done):
                break
        results = [f.result()[0] for f in futures.as_completed(to_do)]
        assert all(results)
        
def test_check_removing_lockfile_after_occuring_exception(tmpdir):
    # GIVEN: direcotry
    # WHEN: a wrapped function throws exception
    # THEN: collectly remove lockfile.lock
    p = tmpdir.mkdir("sub")
    @lock(path=str(p))
    def failed_func():
        raise Exception
    try:
        failed_func()
    except:
        pass
    lockfile = p / 'lockfile.lock'
    with pytest.raises(AssertionError):
        assert lockfile.exists()
        
def test_watch(tmpdir):
    # GIVEN: direcotry
    # WHEN: a lockfile exists
    # THEN: watch wrapper returns value
    p = tmpdir.mkdir("sub")
    lockfile = p / 'lockfile.lock'
    lockfile.open('w').close()
    @watch(filename='lockfile.lock', path=str(p))
    def wrapped_func():
        pass
    with pytest.raises(AssertionError):
        assert wrapped_func(), 'a lockfile exists.'
        

    
        

