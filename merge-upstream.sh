#!/bin/sh

set -eux

# git checkout develop

git fetch https://github.com/pyload/pyload develop:upstream-develop

# rebase: change commit ids
# git rebase upstream-develop

git stash -m "merge-upstream.sh $(date -Is)"

# merge: preserve commit ids
git merge upstream-develop

git stash pop
