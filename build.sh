#!/bin/bash
set -e
echo "================================="
echo "Starting Application Build"
echo "================================="
VERSION="${APP_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo dev)}"
rm -rf build
mkdir -p build
cp -r app requirements.txt Dockerfile build/
find build -name '__pycache__' -prune -exec rm -rf {} +
cat > build/build-info.txt <<INFO
Application: Session 16 Calculator API
Version:     ${VERSION}
Build Date:  $(date -u '+%Y-%m-%d %H:%M:%S UTC')
Build Status: SUCCESS
INFO
tar -czf "build/calculator-${VERSION}.tar.gz" -C build app requirements.txt Dockerfile build-info.txt
echo ""
echo "Build files:"
ls -la build
echo ""
echo "Build completed successfully."
