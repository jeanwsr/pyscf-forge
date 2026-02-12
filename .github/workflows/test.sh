#!/usr/bin/env bash
  
set -e

cd ./pyscf
pytest -k 'not _slow' sftda/ grad/tduks_sf
