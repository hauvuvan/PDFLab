#!/bin/zsh
cd "${0:A:h}"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv || exit 1
fi
.venv/bin/python -m pip install -r requirements.txt || { echo 'Không cài được thư viện. Kiểm tra kết nối mạng.'; read; exit 1; }
(sleep 2; open http://127.0.0.1:8765) &
.venv/bin/python app.py
