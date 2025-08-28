#!/bin/bash

echo "🔄 Restarting Lumia service..."

# Stop the service
systemctl --user stop lumia.service

# Wait a moment
sleep 2

# Start the service
systemctl --user start lumia.service

# Wait for startup
sleep 3

# Check status
echo "📊 Service status:"
systemctl --user status lumia.service --no-pager

echo ""
echo "✅ Lumia restarted successfully!"
echo "🌐 Access at: http://localhost:8002"
echo "📚 API docs: http://localhost:8002/docs" 