#!/usr/bin/env bash
# watch_and_restart.sh – ตรวจจับการแก้ไขไฟล์ update_workflow.py และรีสตาร์ท n8n Docker container
# ---------------------------------------------------------------
WATCH_FILE="/home/krit/my-office/n8n-ai-agent/shopee-getproduct-csv/update_workflow.py"
CONTAINER_ID="9a4d77b5dd0e"

# ตรวจสอบว่าคำสั่ง inotifywait มีอยู่หรือไม่
if ! command -v inotifywait >/dev/null 2>&1; then
  echo "Error: inotifywait ไม่พบ. กรุณาติดตั้งแพคเกจ 'inotify-tools' (Debian/Ubuntu) หรือใช้วิธีอื่น" >&2
  exit 1
fi

echo "กำลังเฝ้าดูการแก้ไขไฟล์: $WATCH_FILE"
while inotifywait -e close_write "$WATCH_FILE"; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') – ไฟล์ถูกแก้ไข, รีสตาร์ท n8n container ($CONTAINER_ID)"
  docker restart "$CONTAINER_ID"
done
