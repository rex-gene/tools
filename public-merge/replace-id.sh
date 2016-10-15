#!/bin/bash

count=0
outputName="__patch"

function convert_format() {
  files=$(find "$1")
  for file in $files
  do
    if [ -f $file ]; then
      dox2unix $file
    fi
  done
}

function make_patch() {
  cd $1
  res=$(grep $2 . -rl | grep -v 'R\$' | grep -v "$outputName")
  for fileName in $res
  do
    if [ -f "$fileName" ]; then
      dos2unix "$fileName"
      sed "s/$2/$3/g" "$fileName" > newFile
      if [ "$fileName" != "." ]; then
        if [ ! -d "$outputName/${fileName:2}" ]; then
          mkdir -p "$outputName/${fileName:2}"
        fi
        diff "$fileName" "newFile" > "$outputName/${fileName:2}/$count"
        rm -f newFile
        count=$((count + 1))
      fi
    fi
  done
  cd - > /dev/null
}

cp -r "$1" backup

convert_format "$1"

for line in $(cat out)
do
  array=($(echo $line | tr ',' ' '))
  make_patch "$1" ${array[1]} ${array[2]}
done

cd "$1"
patchFiles=$(find $outputName | xargs dirname | sort | uniq)

for file in $patchFiles
do
  if [ "$file" != "$outputName" ] && [ "$file" != "." ]; then
    fileList=$(find $file)
    for f in $fileList
    do
      srcFile="${file:8}"
      if [ -f "$f" ] && [ -f "$srcFile" ]; then
        patch "$srcFile" "$f"
        sleep 0.1
      fi
    done
  fi
done

rm -fr $outputName
cd - > /dev/null
