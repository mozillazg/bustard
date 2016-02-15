# bustard

[![Build Status](https://travis-ci.org/mozillazg/bustard.svg?branch=master)](https://travis-ci.org/mozillazg/bustard)

A tiny web framework powered by Python.


## features

* template
* router
* orm
* wsgi server


## usage

```python
from bustard.app import Bustard

app = Bustard()

@app.route('/')
def helloword(request):
    return 'hello world'
```
