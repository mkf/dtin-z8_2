from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response
from struct import pack, unpack
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
import urllib
import os.path

class FileWithIndex:

    class WrongSetOfFields(Exception):
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
        return i//4

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

    def add(self, r):
        if set(r.keys()) != self._FIELDS__SET_OF_NAMES:
            print(r, self._FIELDS__SET_OF_NAMES)
            raise self.WrongSetOfFields()
        i = self._make_new_index() + 1
        for k, t in self._FIELDS__TYPES:
            if t:
                assert type(r[k]) is list
                for kk in r[k]:
                    assert type(kk) is str
            else:
                assert type(r[k]) is str
            self._field(r[k])
        return i

    def __getitem__(self, i):
        gsr = self.get_split_row(i-1)
        sr = iter(gsr)
        r = {}
        bs = lambda x: str(x, encoding="UTF-8")
        for k, t in self._FIELDS__TYPES:
            if t:
                rr = []
                while True:
                    nsr = next(sr)
                    if(len(nsr) == 0):
                        break
                    rr.append(bs(nsr))
                r[k] = rr
            else:
                r[k] = bs(next(sr))
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
            raise HTTPNotFound()

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

def _validate_url(u):
    tokens = urllib.parse.urlparse(u)
    return getattr(tokens, 'netloc') and getattr(tokens, 'scheme') in {'http', 'https', 'ftp'}

def _validate(r):
    for i in ('name', 'photo', 'ingredients', 'steps'):
        if i not in r:
            raise ValueError(i+" not in "+str(r))
    for i in ('name', 'photo'):
        if type(r[i]) is not str:
            raise ValueError(i+"is not str, :"+str(r[i]))
        if "\n" in r[i]:
            raise ValueError("a newline in "+i)
    for i in ('ingredients', 'steps'):
        if type(r[i]) is not list:
            raise ValueError(i+"is not list, :"+str(r[i]))
        if len(r[i])<1:
            raise ValueError("length of "+i+" is less than one")
        for v in r[i]:
            if type(v) is not str:
                raise ValueError("in "+i+":"+str(r[i])+" the "+v+" is not str")
            if len(v)<2:
                raise ValueError(v+" is less than 2 chars")
            if "\n" in v:
                raise ValueError("a newline in "+i)
    if len(r['name'])<4:
        raise ValueError(r['name']+" is less than 4 chars")
    if not _validate_url(r['photo']):
        raise ValueError("photo url deemed invalid")
    return True
    #return 'name' in r and 'photo' in r and 'ingredients' in r and 'steps' in r and \
    #type(r['name']) is str and type(r['photo']) is str and \
    #type(r['ingredients']) is list and type(r['steps']) is list and \
    #len(r['name'])>3 and "\n" not in r['name'] and "\n" not in r['photo'] and _validate_url(r['photo']) and \
    #len(r['ingredients'])>0 and len(r['steps'])>0 and \
    #all(all((type(i) is str and len(i)>1 and "\n" not in i) for i in rr) for rr in (r['ingredients'], r['steps']))

@view_config(route_name='recipe_one', renderer='one.jinja2')
def recipe_one(request):
    id = request.matchdict['id']
    try:
        id = int(id)
    except ValueError as e:
        raise e
    return fwi[id]


@view_config(route_name='recipe_new', request_method='GET', renderer='form.jinja2')
def recipe_new_form(request):
    return {}

@view_config(route_name='recipe_new', request_method='POST', renderer='done.jinja2')
def recipe_new_post(request):
    p = request.POST
    if set(p.keys()) != FileWithIndex._FIELDS__SET_OF_NAMES:
        return HTTPBadRequest()
    name = p.getall('name')
    photo = p.getall('photo')
    if len(name)>1 or len(photo)>1:
        return HTTPBadRequest()
    r = {
        'name': name[0],
        'photo': photo[0],
        'ingredients': [jeden for jeden in p.getall('ingredients') if len(jeden)>0],
        'steps': [jeden for jeden in p.getall('steps') if len(jeden)>0]
        }
    try:
        _validate(r)
    except ValueError as e:
        raise HTTPBadRequest(e)
    return {"number": fwi.add(r)}


@view_config(route_name='recipe_api_new', renderer='json')
def recipe_api_new(request):
    j = request.json_body
    try:
        _validate(j)
    except ValueError as e:
        raise HTTPBadRequest(e)
    return fwi.add(j)

@view_config(route_name='recipe_api_one', renderer='json')
def recipe_api_one(request):
    id = request.matchdict['id']
    try:
        id = int(id)
    except ValueError as e:
        raise e
    return fwi[id]


config = Configurator()
config.add_route('recipe_new', '/recipe/new')
config.add_route('recipe_one', '/recipe/{id}')
config.add_route('recipe_api_new', '/recipe/api/new')
config.add_route('recipe_api_one', '/recipe/api/{id}')
config.include('pyramid_jinja2')
thisDirectory = os.path.dirname(os.path.realpath(__file__))
config.add_jinja2_search_path(thisDirectory)
config.commit()
jinja2_env = config.get_jinja2_environment()
jinja2_env.autoescape = False
config.scan()

app = config.make_wsgi_app()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('', 6543, app)
    server.serve_forever()
