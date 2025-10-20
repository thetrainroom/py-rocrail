#!/bin/bash
# Quick start script for Rocrail test server

set -e

ACTION=${1:-start}

case "$ACTION" in
    start)
        echo "Starting Rocrail Docker test server..."
        docker-compose up -d
        echo ""
        echo "Waiting for server to be ready..."
        sleep 5
        echo ""
        echo "✓ Rocrail server is running on localhost:8051"
        echo ""
        echo "Test connection with:"
        echo "  python -c 'from pyrocrail.pyrocrail import PyRocrail; pr = PyRocrail(\"localhost\", 8051); pr.start(); print(\"Connected!\"); pr.stop()'"
        echo ""
        echo "Run integration tests with:"
        echo "  pytest tests/integration/test_docker_rocrail.py -v"
        echo ""
        echo "View logs with:"
        echo "  docker-compose logs -f"
        ;;

    stop)
        echo "Stopping Rocrail Docker test server..."
        docker-compose down
        echo "✓ Server stopped"
        ;;

    restart)
        echo "Restarting Rocrail Docker test server..."
        docker-compose restart
        sleep 5
        echo "✓ Server restarted"
        ;;

    logs)
        docker-compose logs -f rocrail
        ;;

    status)
        docker-compose ps
        ;;

    build)
        echo "Building Rocrail Docker image..."
        docker-compose build
        echo "✓ Build complete"
        ;;

    clean)
        echo "Removing Rocrail Docker container and volumes..."
        docker-compose down -v
        echo "✓ Cleanup complete"
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|logs|status|build|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Rocrail test server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  logs    - View server logs (follow mode)"
        echo "  status  - Check server status"
        echo "  build   - Build the Docker image"
        echo "  clean   - Remove container and volumes"
        exit 1
        ;;
esac
