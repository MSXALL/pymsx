#! /bin/bash

if [ "$#" -eq 1 ]; then
	DURATION=$1
else
	DURATION=5
fi

ORGD=`pwd`
DIR=`mktemp -d`
cp *py zex*.com $DIR/

pushd $DIR
sed -i 's/self.debug.*/pass/g' z80.py
python3 -m cProfile ./zex.py $DURATION | tee $ORGD/profile.txt

rm -rf $DIR
