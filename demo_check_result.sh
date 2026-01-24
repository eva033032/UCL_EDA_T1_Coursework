#!/bin/bash

# 1. 設定搜尋關鍵字
if [ -z "$1" ]; then
    SEARCH_KEY="ARRD4_MOUSE"
else
    SEARCH_KEY=$1
fi

echo "🔍 正在所有 Workers 上搜尋包含 '$SEARCH_KEY' 的數據..."

# 2. 執行 Ansible 並捕捉輸出
# ★★★ 修正重點：移除了 --ignore-errors ★★★
# 我們改用 2>/dev/null 把 Ansible 的錯誤輸出丟掉，只保留標準輸出
OUTPUT=$(ansible -i inventory.ini workers -m shell \
    -a "cat /home/almalinux/*${SEARCH_KEY}*parse.out" \
    2>/dev/null)

# 3. 清理雜訊
# 過濾掉 Ansible 的系統回傳字串，只留下真正的 CSV 內容
CLEAN_DATA=$(echo "$OUTPUT" | grep -v "FAILED" | grep -v "rc=" | grep -v "SUCCESS" | grep -v "CHANGED" | grep -v ">>" | grep -v "No such file")

echo "---------------------------------------------------"

# 4. 智慧判斷
if [ -n "$CLEAN_DATA" ]; then
    # 有抓到資料 -> 印出來
    echo "$CLEAN_DATA"
    echo "---------------------------------------------------"
    echo "🎉 DEMO SUCCESS！ (成功產出 CSV 結果)"
else
    # 沒抓到資料 -> 提示等待
    echo "⏳ 尚未發現結果。"
    echo "   (可能原因：Worker 還在運算中，請再等 30 秒後重試)"
fi