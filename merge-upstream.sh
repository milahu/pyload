#!/bin/sh

set -eux

# git checkout develop

git fetch https://github.com/pyload/pyload develop:upstream-develop

# rebase: change commit ids
# git rebase upstream-develop

# merge: preserve commit ids
git merge upstream-develop
