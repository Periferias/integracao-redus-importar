#!/bin/sh

if [ ! -f "$CSV_FILE_PATH" ]; then
  _length=54
  _status="erro"
  _message="Arquivo não encontrado"
else
  python setup.py

  if [ $? -eq 0 ]; then
    _length=68
    _status="sucesso"
    _message="Importação realizada com sucesso"
  else
    _length=58
    _status="erro"
    _message="Importação não realizada"
  fi
fi

echo "$_status: $_message" >&2

echo "HTTP/1.1 200 OK"
echo "Content-Type: application/json"
echo "Content-Length: $_length"
echo "Connection: close"
echo ""
echo "{\"status\":\"$_status\",\"message\":\"$_message\"}"
