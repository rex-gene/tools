#!/bin/bash

sed -i "s/\"useMergedTexture\": true,/\"useMergedTexture\": false,/g" $1
sed -i "s/\"resourceType\": 1/\"resourceType\": 0/g" $1

mv $1 ${1:0:-10}json
