from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response
from tinydb import TinyDB, Query, where
from jsonschema import validate
from struct import pack, unpack


class FileWithIndex:

    class WrongSetOfFields(Exception):
        pass

    class NotFound(Exception):
        pass

    _FIELDS = ["name", "photo", ["ingredients"], ["steps"]]
    for notation in _FIELDS:
        t = type(notation)
        if t is str:
            pass
        elif t is list:
            assert len(notation) == 1
        else:
            raise TypeError()
    _FIELDS__NAMES_OF = [(i[0] if type(i) is list else i) for i in _FIELDS]
    _FIELDS__SET_OF_NAMES = set(_FIELDS__NAMES_OF)
    _FIELDS__TYPES = [((k[0], True) if type(k) is list else (k, False))
                      for k in _FIELDS]
    _PACKING = '<i'
    _SEP = b"\n"  # b"\x00"

    def __init__(self, index_filename: str, storage_filename: str):
        self._index_filename: str = index_filename
        self._index_f = open(index_filename, "a+b", buffering=0)
        self._storage_filename: str = storage_filename
        self._storage_f = open(storage_filename, "a+b", buffering=0)

    def _make_new_index(self):
        self._storage_f.seek(0, 2)
        d = self._storage_f.tell()
        self._index_f.seek(0, 2)
        i = self._index_f.tell()
        self._index_f.write(pack(self._PACKING, d))
        return i

    def _field(self, b: str):
        if type(b) is list:
            for i in b:
                self._field(i)
        else:
            b = bytes(b, encoding="UTF-8")
            assert b"\n" not in b
            assert b"\n"[0] not in b
            self._storage_f.write(b)
        self._storage_f.write(self._SEP)

    def add(self, **r):
        if set(r.keys()) != self._FIELDS__SET_OF_NAMES:
            print(r, self._FIELDS__SET_OF_NAMES)
            raise self.WrongSetOfFields()
        i = self._make_new_index() + 1
        for k in self._FIELDS__NAMES_OF:
            self._field(r[k])
        return i

    def __getitem__(self, i):
        gsr = self.get_split_row(i-1)
        sr = iter(gsr)
        r = {}
        for k, t in self._FIELDS__TYPES:
            if t:
                rr = []
                while True:
                    nsr = next(sr)
                    if(len(nsr) == 0):
                        break
                    rr.append(nsr)
                r[k] = rr
            else:
                r[k] = next(sr)
        assert len(next(sr)) == 0
        try:
            next(sr)
        except StopIteration:
            pass
        else:
            raise AssertionError(str(gsr))
        return r

    def get_split_row(self, i):
        return self.get_raw_row(i).split(self._SEP)

    def get_raw_row(self, i):
        self._index_f.seek(0, 2)  # index is now at EOF
        e = self._index_f.tell()  # e is now how long index is

        if e <= i*4:
            raise self.NotFound()

        self._index_f.seek(i*4, 0)  # index is now at i-th entry
        o = unpack(self._PACKING, self._index_f.read(4))[
            0]  # o is now the i-th entry

        self._storage_f.seek(o, 0)  # storage is now at i-th entry (at o)

        if e != self._index_f.tell():
            o = (unpack(self._PACKING, self._index_f.read(4))[0]) - o
            return self._storage_f.read(o)
        else:
            return self._storage_f.read()


fwi = FileWithIndex("recipes.idx", "recipes.dat")


@view_config(route_name='recipe_one', renderer='string')
def recipe_one(request):
    id = request.matchdict['id']
    try:
        id = int(id)
    except ValueError as e:
        raise e
    return fwi[id]


@view_config(route_name='recipe_new', renderer='string')
def recipe_new(request):
    return fwi.add(**{"name": "tytul", "photo": "foto", "ingredients": ["ia", "ib", "ic"], "steps": ["sa", "sb"]})


@view_config(route_name='recipe_api_new', renderer='string')
def recipe_api_new(request):
    return fwi.add(**{"name": "tytul", "photo": "foto", "ingredients": ["ia", "ib", "ic"], "steps": ["sa", "sb"]})


config = Configurator()
config.add_route('recipe_new', '/recipe/new')
config.add_route('recipe_one', '/recipe/{id}')
config.add_route('recipe_api_new', '/recipe/api/new')
config.scan()

app = config.make_wsgi_app()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('', 6543, app)
    server.serve_forever()
