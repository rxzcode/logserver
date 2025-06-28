#!/bin/bash
rm -f .coverage*
for svc in log auth tenant; do
    PYTHONPATH=app/$svc pytest app/$svc/tests \
        --cov=core \
        --cov=routes \
        --cov-append \
        --cov-config=setup.cfg --cov-report=term
done
coverage combine
coverage html -d coverage

# Check if port 8000 is already in use
if lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ Server already running on port 8000"
else
    echo "🚀 Starting server on port 8000..."
    python3 -m http.server 8000 -d coverage &
    sleep 1
fi

# Open the browser based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8000
elif command -v xdg-open >/dev/null; then
    xdg-open http://localhost:8000
else
    echo "🌐 Please open http://localhost:8000 in your browser"
fi
