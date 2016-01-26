# bustard

A tiny web framework powered by Python.


## features

* template
* router
* view
* model
* wsgi server


## usage

```python
from bustard.app import Bustard

app = Bustard()

@app.route('/')
def helloword(request):
    return 'hello world'
```
