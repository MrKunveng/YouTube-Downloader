#!/bin/bash

# Script to update repository with deployment files
# Run this script to push all changes to GitHub and Hugging Face

echo "🚀 Updating repository with deployment files..."
echo ""

# Check git status
echo "📋 Checking git status..."
git status

echo ""
echo "📦 Files ready to push:"
git ls-files | grep -E "Dockerfile|README|DEPLOY|HF_|railway|render|fly|app.py|dockerignore"

echo ""
echo "🔄 Pushing to GitHub (origin)..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
else
    echo "❌ Failed to push to GitHub. Check your connection and credentials."
fi

echo ""
echo "🔄 Pushing to Hugging Face Spaces (hf)..."
git push hf main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to Hugging Face!"
    echo ""
    echo "🎉 Your app will auto-deploy on Hugging Face Spaces!"
    echo "📍 Check: https://huggingface.co/spaces/MrKunveng/YouTube_downloader"
else
    echo "❌ Failed to push to Hugging Face. Check your HF credentials."
fi

echo ""
echo "✨ Done!"
