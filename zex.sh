#! /bin/bash

DIR=`mktemp -d`
cp *py zex*.com $DIR/

pushd $DIR
sed -i 's/self.debug.*/pass/g' z80.py
pypy3 -O ./zex.py
popd

rm -rf $DIR
