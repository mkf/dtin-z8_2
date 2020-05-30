let
  pkgs = import <nixpkgs> {};
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (python-packages: with python-packages; [
        marshmallow pyramid_jinja2 pyramid
        tinydb
        python-language-server
        pylint autopep8
        jsonschema
      ]))
  ];
}
