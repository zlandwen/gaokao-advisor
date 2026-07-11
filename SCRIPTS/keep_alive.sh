#!/bin/bash
# 雪峰人AI 自动保活脚本
URL="https://boundary-product-replacement-springer.trycloudflare.com"
while true; do
    curl -s --get --data-urlencode "name=燃爆" http://localhost:8081/api/get_answers > /dev/null 2>&1
    curl -s http://localhost:9092/ > /dev/null 2>&1
    curl -s "$URL/" > /dev/null 2>&1
    sleep 240
done
