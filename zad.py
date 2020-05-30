from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response
from tinydb import TinyDB, Query, where
from jsonschema import validate

class TableFile:

    class WrongFieldSize(Exception):
        pass

    class WrongSetOfFields(Exception):
        pass

    _LAYOUT_SCHEMA = {
        "type": "object",
        "patternProperties": { "^[a-z]{3,15}$": {"type": "integer", "exclusiveMinimum": 0} },
        "additionalProperties": false 
    }
    
    def __init__(self, filename : str, layout : dict):
        validate(layout, _LAYOUT_SCHEMA)
        self._filename : str = filename
        self._fileopen = open(filename, "a+b")
        self._layout = layout
        offsets = {}
        order = []
        acc = 0
        for k, v in layout.items():
            order.append((k, v, acc, acc+v))
            offsets[k] = (acc, acc + v)
            acc += v
        self._offsets = offsets
        self._order = order
        self._rowsize = acc

    @property
    def row_size(self) -> int:
        return self._row_size

    @property
    def layout(self) -> dict:
        return self._layout.copy()

    @property
    def filename(self) -> str:
        return self._filename

    def _field(self, b, n):
        assert type(b) is bytes
        if len(b)!=n:
            raise WrongFieldSize()
        self._fileopen.write(b)

    def add(self, **r):
        if set(r.keys())!=set(self._layout.keys()):
            raise WrongSetOfFields()
        for k, v, _, _ in self._order:
            _field(r[k], v)


db = TinyDB('db.json')
table = db.table('recipes')

latest = 0
for i in table.all():
    j = i['id']
    if j>latest:
        latest = j

@view_config(route_name='recipe_one')
def recipe_one(request):
    id = request.matchdict['id']
    try:
        id = int(id)
    except ValueError as e:
        raise e
    found = table.search(where('id') == id)
    assert len(found) <= 1
    if len(found) == 0:
        return 404


@view_config(route_name='recipe_new')
def recipe_new(request):
    pass


@view_config(route_name='recipe_api_new')
def recipe_api_new(request):
    pass


config = Configurator()
config.add_route('recipe_one', '/recipe/{id}')
config.add_route('recipe_new', '/recipe/new')
config.add_route('recipe_api_new', '/recipe/api/new')
config.scan()

app = config.make_wsgi_app()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('', 6543, app)
    server.serve_forever()
