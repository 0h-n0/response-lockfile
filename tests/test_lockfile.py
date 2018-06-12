from pathlib import Path

import pytest

from view_lockfile import SimpleLockFile
from view_lockfile import lock_view
from view_lockfile import watch_lockfile



@pytest.mark.parametrize('root_path',
                         ['/tmp', '~', '.'])
def test_root_path(root_path):
    SimpleLockFile.set_root_path(root_path)
    assert SimpleLockFile.root_path == str(Path(root_path).expanduser().resolve())


@pytest.mark.parametrize('root_path',
                         ['/hoge/hoge', '/hoge/~/hoge'])
def test_root_path_fail_cases(root_path):
    with pytest.raises(ValueError):
        SimpleLockFile.set_root_path(root_path)

    
def test_read():
    # GIVEN an initialized tmpfile
    pass
    
    

    
        

