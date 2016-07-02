#!/bin/bash


files=$(find -name "*.plist")
for file in $files
do
    python ~/tools/unpack/unpack_plist.py ${file:2:-6}
done
