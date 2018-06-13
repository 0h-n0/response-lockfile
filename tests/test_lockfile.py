from pathlib import Path

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



def success_func():
    pass

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
        
        
        
        
    
        
def test_read():
    # GIVEN an initialized tmpfile
    pass
    
    

    
        

