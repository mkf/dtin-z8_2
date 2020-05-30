from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.response import Response
from tinydb import TinyDB, Query, where

db = TinyDB('db.json')
table = db.table('recipes')


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
