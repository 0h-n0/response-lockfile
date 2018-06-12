# response-lockfile

> Note

 Response-lockfile adapts 'one file lock system'.

## Coencept


## Dependencies

- requrests

## How to use

The following example is based on Django project. With this module, you can lock a view method in your app.

```settings.py

from response_lockfile import ReponseLockFile

# ~~~

ResponseLockFile.set_root_path('/home/hoge/')
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

