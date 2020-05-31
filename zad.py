from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response
from tinydb import TinyDB, Query, where
from jsonschema import validate
from struct import pack

class FileWithIndex:

    class WrongSetOfFields(Exception):
        pass

    _FIELDS = ["name", "photo", ["ingredients"], ["steps"]]
    _FIELDS__NAMES_OF = [_get_field_name(i) for i in _FIELDS]
    _FIELDS__SET_OF_NAMES = set(_FIELDS__NAMES_OF)
    _FIELDS__TYPES = [(k[0], True) if k is list else (k, False) for k in _FIELDS]
    _PACKING = '<i'
    _SEP = b"\n"  # b"\x00"
    
    def __init__(self, index_filename : str, storage_filename : str):
        self._index_filename : str = index_filename
        self._index_f = open(index_filename, "a+b", buffering=0)
        self._storage_filename : str = storage_filename
        self._storage_f = open(storage_filename, "a+", buffering=0)

    def _make_new_index(self):
        self._storage_f.seek(0, 2)
        i = self._storage_f.tell()
        self._index_f.seek(0, 2) # pretty surely totally redundant
        self._index_f.write(pack(_PACKING, i))
        return i

    @staticmethod
    def _get_field_name(notation):
        t = type(notation)
        if t is str:
            return notation
        elif t is list:
            assert len(notation)==1
            return notation[0]
        else:
            raise TypeError()


    def _field(self, b):
        assert b"\n" not in b
        assert b"\n"[0] not in b
        if type(b) is list:
            for i in b:
                _field(i)
        else:
            self._storage_f.write(b)
        self._storage_f.write(_SEP)

    def add(self, **r):
        if set(r.keys())!=_FIELDS__SET_OF_NAMES:
            raise WrongSetOfFields()
        i = _make_new_index()
        for k, v, _, _ in self._order:
            _field(r[k], v)
        return i

    def __getitem__(self, i):
        sr = iter(get_split_row(i))
        r = {}
        for k, t in _FIELDS__TYPES:
            r[k] = next(sr)
            if t:
                assert len(next(sr))==0
        try:
            next(sr)
        except StopIteration:
            pass
        else:
            raise AssertionError()


    def get_split_row(self, i):
        return get_raw_row.split(_SEP)

    def get_raw_row(self, i):
        self._index_f.seek(0, 2)
        e = self._index_f.tell()

        self._index_f.seek(i*4, 0)
        o = unpack(_PACKING, self._index_f.read(4))[0]

        self._storage_f.seek(o, 0)

        if e<=(i+1)*4:
            self._index_f.seek(4, 1)
            o = (unpack(_PACKING, self._index_f.read(4))[0]) - o
            return self._storage_f.read(o)
        else:
            return self._storage_f.read()

fwi = FileWithIndex("recipes.idx", "recipes.dat")

@view_config(route_name='recipe_one')
def recipe_one(request):
    id = request.matchdict['id']
    try:
        id = int(id)
    except ValueError as e:
        raise e
    return fwi[id]


@view_config(route_name='recipe_new')
def recipe_new(request):
    return fwi.add({"name": "tytul", "photo": "foto", "ingredients": ["ia", "ib", "ic"], "steps": ["sa", "sb"]})


@view_config(route_name='recipe_api_new')
def recipe_api_new(request):
    return fwi.add({"name": "tytul", "photo": "foto", "ingredients": ["ia", "ib", "ic"], "steps": ["sa", "sb"]})


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
