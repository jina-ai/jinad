#!/usr/bin/env bash

# Requirements
# npm install -g git-release-notes
# pip install twine wheel

set -ex

RELEASENOTE='./node_modules/.bin/git-release-notes'
VER_TAG='VERSION: str = '
INIT_FILE='jinad/config.py'
LOG_FILE='./CHANGELOG.md'

function make_release_note {
  ${RELEASENOTE} ${LAST_VER}..HEAD .github/release-template.ejs > ./CHANGELOG.tmp
  head -n10 ./CHANGELOG.tmp
  printf '\n%s\n\n%s\n%s\n\n%s\n\n%s\n\n' \
    "$(cat ./CHANGELOG.md)" \
    "<a name="release-note-${RELEASE_VER//\./-}"></a>" \
    "## Release Note (\`${RELEASE_VER}\`)" \
    "> Release time: $(date +'%Y-%m-%d %H:%M:%S')" \
    "$(cat ./CHANGELOG.tmp)" > ${LOG_FILE}
}

function clean_build {
    rm -rf dist
    rm -rf *.egg-info
    rm -rf build
}

function pub_pypi {
  clean_build
  python setup.py sdist
  twine upload dist/*
  clean_build
}

function escape_slashes {
    sed 's/\//\\\//g'
}

function update_ver_line {
  local OLD_LINE_PATTERN=$1
  local NEW_LINE=$2
  local FILE=$3
  local NEW=$(echo "${NEW_LINE}" | escape_slashes)
  echo ${OLD_LINE_PATTERN}
  echo ${NEW}
  echo ${FILE}
  sed -i '/'"${OLD_LINE_PATTERN}"'/s/.*/'"    ${NEW}"'/' "${FILE}"
  head -n10 ${FILE}
}

function git_commit {
  git config --local user.email "dev-bot@jina.ai"
  git config --local user.name "Jina Dev Bot"
  git tag "v$RELEASE_VER" -m "$(cat ./CHANGELOG.tmp)"
  git add $INIT_FILE ${LOG_FILE}
  git commit -m "chore(version): the next version will be ${NEXT_VER}"
}

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" != "main" ]]; then
  printf "You are not at main branch, exit\n";
  exit 1;
fi

LAST_UPDATE=`git show --no-notes --format=format:"%H" $BRANCH | head -n 1`
LAST_COMMIT=`git show --no-notes --format=format:"%H" origin/$BRANCH | head -n 1`

if [[ "$LAST_COMMIT" != "$LAST_UPDATE" ]]; then
  printf "Your local $BRANCH is behind the remote mater, exit\n";
  exit 1;
fi

export RELEASE_VER=$(python -c 'from jinad.config import FastAPIConfig;api=FastAPIConfig();print(api.VERSION)')
printf "to-be released version: \e[1;32m$RELEASE_VER\e[0m\n"

LAST_VER=$(git tag -l | sort -V | tail -n1)
printf "last version: \e[1;32m$LAST_VER\e[0m\n"

NEXT_VER=$(echo $RELEASE_VER | awk -F. -v OFS=. 'NF==1{print ++$NF}; NF>1{$NF=sprintf("%0*d", length($NF), ($NF+1)); print}')
printf "bump main version: \e[1;32m$NEXT_VER\e[0m\n"

make_release_note

pub_pypi

VER_TAG_NEXT=$VER_TAG"'"${NEXT_VER#"v"}"'"
update_ver_line "$VER_TAG" "$VER_TAG_NEXT" $INIT_FILE

git_commit