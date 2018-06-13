[![LICENCE](https://img.shields.io/badge/LICENCE-MIT-brightgreen.svg)](https://github.com/0h-n0/simple-lock)
[![PYTHON version](https://img.shields.io/badge/python-3.5,3.6-blue.svg)](https://github.com/0h-n0/simple-lock)
[![PyPI version](https://badge.fury.io/py/simple-lock.svg)](https://badge.fury.io/py/simple-lock)
[![Build Status](https://travis-ci.org/0h-n0/simple-lock.svg?branch=master)](https://travis-ci.org/0h-n0/simple-lock)
[![codecov](https://codecov.io/gh/0h-n0/view-lockfile/branch/master/graph/badge.svg)](https://codecov.io/gh/0h-n0/view-lockfile)
[![Maintainability](https://api.codeclimate.com/v1/badges/9a8b4b39d3673ccb6db6/maintainability)](https://codeclimate.com/github/0h-n0/simple-lock/maintainability)
[![BCH compliance](https://bettercodehub.com/edge/badge/0h-n0/simple-lock?branch=master)](https://bettercodehub.com/)



# simple-lock

> Note

 Simple-lockfile uses a file as a lock system.

## Coencept

## How to use

The following example is based on Django project. With this module, you can lock a view method in your app.

```settings.py

from simple_lock import SimpleLock

# ~~~

File.set_root_path('/home/hoge/')
# A lockfile is created in the root_path directory without setting path as arguments.

```


```app/view.py

from response_lockfile import lock_lockfile

# ~~~

@lock_view(name='lockfile1.lock')
def view():
    #some_logic
    return HttpResponse()
```

This decoreator creates lockfile1.lock and releases.

```app2/view.py

from response_lockfile import watch_lockfile

# ~~~

@watch_lockfile(name='lockfile1.lock')
def view():
    return HttpResponse()
```

If lockfile1.lock exists when execute app2/view:view, this decoreator returns a http response.

 