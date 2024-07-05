#!/bin/sh
# install dependencies of pyload
# https://github.com/milahu/nur-packages/raw/master/pkgs/python3/pkgs/pyload/pyload.nix
NIXPKGS_ALLOW_UNFREE=1 exec nix-shell -E '
  with import <nixpkgs> { };
  python3.pkgs.callPackage ./nix/pyload.nix {
    python3 = pkgs.python3 // {
      pkgs = pkgs.python3.pkgs // {
        flask-session2 = python3.pkgs.callPackage ./nix/flask-session2.nix { };
      };
    };
  }
'
