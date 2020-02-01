#! /bin/sh

rm -f .coverage
coverage run --branch ./test.py
rm -rf htmlcov
coverage html
