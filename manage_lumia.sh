#!/bin/bash

# Lumia Service Management Script

SERVICE_NAME="lumia.service"

case "$1" in
    start)
        echo "Starting Lumia service..."
        systemctl --user start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping Lumia service..."
        systemctl --user stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting Lumia service..."
        systemctl --user restart $SERVICE_NAME
        ;;
    status)
        echo "Lumia service status:"
        systemctl --user status $SERVICE_NAME
        ;;
    enable)
        echo "Enabling Lumia service (auto-start on boot)..."
        systemctl --user enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling Lumia service..."
        systemctl --user disable $SERVICE_NAME
        ;;
    logs)
        echo "Lumia service logs:"
        journalctl --user -u $SERVICE_NAME -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Lumia service"
        echo "  stop    - Stop the Lumia service"
        echo "  restart - Restart the Lumia service"
        echo "  status  - Show service status"
        echo "  enable  - Enable auto-start on boot"
        echo "  disable - Disable auto-start on boot"
        echo "  logs    - Show service logs"
        exit 1
        ;;
esac 