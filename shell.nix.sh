#!/bin/sh

# unfree pkgs: unrar ...
export NIXPKGS_ALLOW_UNFREE=1

exec nix-shell
