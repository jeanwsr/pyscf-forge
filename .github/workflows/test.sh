#!/usr/bin/env bash
  
set -e

cd ./pyscf
pytest -k 'not _slow' sftda
pytest -k 'not _slow' grad/test/test_grad_sftda.py
