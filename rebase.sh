#!/bin/sh

set -eux

# git checkout main

git fetch https://github.com/pyload/pyload develop:develop

git rebase develop
