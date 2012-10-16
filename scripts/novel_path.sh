#!/bin/bash
base='/home/piglei/webapps/nowater/nowater/novels/'
ids=$@

function get_hash(){
    temp=`echo -n "$1" | md5sum | awk '{print$1}'`
    echo "${base}${temp:0:2}/$1"
}

for id in $ids; do
    get_hash $id
done
