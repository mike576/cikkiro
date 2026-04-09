#!/bin/bash
cd /Users/miklostoth/develop/workspaces/azure-transcription-app
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
python regenerate_analyses.py
