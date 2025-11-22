#!/bin/bash
# Quick demo runner - follows project naming convention

. ./_actvenv.sh
docker-compose up -d
python app.py
