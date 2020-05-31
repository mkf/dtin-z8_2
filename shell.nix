let
  pkgs = import <nixpkgs> {};
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (python-packages: with python-packages; [
        pyramid_jinja2 jinja2 pyramid
        tinydb
        python-language-server
        pylint autopep8
      ]))
  ];
}
