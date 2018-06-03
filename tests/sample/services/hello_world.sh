#!/bin/bash
echo "Working dir: $(pwd)"
dir=$(pwd)
sleep 5
echo "Hello world" > ${dir}/hello_world_output.txt
sleep 5
echo "Follow " $1 >> ${dir}/hello_world_output.txt
sleep 5
echo "Last" $2 >> ${dir}/hello_world_output.txt
