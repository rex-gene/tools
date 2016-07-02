#!/bin/bash

files=$(find -name "*.pkm")

for file in $files
do
  dir=$(dirname $file)
  etc1tool.exe $file --decode
done
