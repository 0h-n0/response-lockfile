[![LICENCE](https://img.shields.io/badge/LICENCE-MIT-brightgreen.svg)](https://github.com/0h-n0/simple-lock)
[![PYTHON version](https://img.shields.io/badge/python-3.5,3.6-blue.svg)](https://github.com/0h-n0/simple-lock)
[![PyPI version](https://img.shields.io/pypi/v/simple-lock.svg)](https://badge.fury.io/py/simple-lock)
[![Build Status](https://travis-ci.org/0h-n0/simple-lock.svg?branch=master)](https://travis-ci.org/0h-n0/simple-lock)
[![codecov](https://codecov.io/gh/0h-n0/simple-lock/branch/master/graph/badge.svg)](https://codecov.io/gh/0h-n0/simple-lock)
[![Maintainability](https://api.codeclimate.com/v1/badges/9a8b4b39d3673ccb6db6/maintainability)](https://codeclimate.com/github/0h-n0/simple-lock/maintainability)
[![BCH compliance](https://bettercodehub.com/edge/badge/0h-n0/simple-lock?branch=master)](https://bettercodehub.com/)



# simple-lock

simple-lock provides lock system as a decorator or with-statement in your code. It is easy to use them.

## Coencept

You can easily implement lock system in your application with modifing a few line. There are mainly two decorator in `simple_lock`. First, `simple_lock.lock` locks function and create a lockfile. After that, other functions refer to the lockfile can't be executed normally. Second, without creating a new lockfile, `simple_lock.watch` watchs a lockfile provieded as one of arguments without creating a new lockfile. 

## How to use

### Lock your function with `simple_lock.lock` decorator.

When a funciton try to create a lockfile and the lockfile already exists. `simple_lock.lock` decorator returns `return_value` like the following codes. 

```test.py

from simple_lock import lock

@lock(filename='simple.lock', path='~/locks',
                              return_value=10)
def sleep():
    import time
    tiem.sleep(10)
    
sleep() # -> 10
```

You can provide a function as 'return_value' argument and arguments of 'return_value'.

```test.py

from simple_lock import lock

def add(a, b):
    return a + b

@lock(filename='simple.lock', path='~/locks',
                              return_value=add
                              a=1, b=1)
def sleep():
    import time
    tiem.sleep(10)
    
sleep() # -> 2
```

`simple_lock.watch` also provides functions similar to `simple_lock.lock`. The difference between `simple_lock.lock` and `simple_lock.watch` is just whether lockfile is created or not.

```test.py

from simple_lock import lock

@watch(filename='simple.lock', path='~/locks',
                              return_value=10)
def sleep():
    import time
    tiem.sleep(10)
    
sleep() # -> 10
```

```test.py

from simple_lock import lock

def add(a, b):
    return a + b

@watch(filename='simple.lock', path='~/locks',
                              return_value=add
                              a=1, b=1)
def sleep():
    import time
    tiem.sleep(10)
    
sleep() # -> 2
```

## References

* https://github.com/benediktschmitt/py-filelock