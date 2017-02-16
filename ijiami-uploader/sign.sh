#!/bin/bash

if [[ 1 != $# ]]; then
  echo $0 "<input-file>"
  exit 1
fi

inputFile=$1

if [ ! -f "$inputFile" ]; then
  echo "$inputFile not exist"
  exit 1
fi

signedFile="${inputFile:0:-4}_signed.apk"

jarsigner -digestalg SHA1 -sigalg MD5withRSA -keystore app1.keystore -storepass 1881982050~\!@ -signedjar "$signedFile" "$1" app1.keystore
zipalign -v 4 "$signedFile" ${inputFile:0:-4}_final.apk

rm -f $inputFile $signedFile
