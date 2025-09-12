#!/bin/bash

# GPT-OSS Docker Container Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs]

COMPOSE_FILE="docker-compose.simple.yml"

case "$1" in
    start)
        echo "🚀 Starting GPT-OSS services..."
        docker compose -f $COMPOSE_FILE up -d
        echo "✅ Services started"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    
    stop)
        echo "⏹️ Stopping GPT-OSS services..."
        docker compose -f $COMPOSE_FILE down
        echo "✅ Services stopped"
        ;;
    
    restart)
        echo "🔄 Restarting GPT-OSS services..."
        docker compose -f $COMPOSE_FILE down
        docker compose -f $COMPOSE_FILE up -d
        echo "✅ Services restarted"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    
    status)
        echo "📊 GPT-OSS services status:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "🔍 Health checks:"
        echo -n "Backend: "
        curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo "Not available"
        echo -n "Frontend: "
        curl -s http://localhost:8501/healthz 2>/dev/null || echo "Not available"
        echo -n "vLLM: "
        curl -s http://localhost:8000/health 2>/dev/null && echo "ok" || echo "Not available"
        ;;
    
    logs)
        SERVICE=$2
        if [ -z "$SERVICE" ]; then
            echo "📜 Showing logs for all services (use './manage.sh logs [vllm|backend|frontend]' for specific service)"
            docker compose -f $COMPOSE_FILE logs --tail=50
        else
            echo "📜 Showing logs for $SERVICE..."
            docker compose -f $COMPOSE_FILE logs --tail=50 gpt-oss-$SERVICE
        fi
        ;;
    
    *)
        echo "GPT-OSS Container Management"
        echo "Usage: $0 {start|stop|restart|status|logs [service]}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services in containers"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status and health"
        echo "  logs    - Show logs (optionally specify: vllm, backend, or frontend)"
        echo ""
        echo "Services:"
        echo "  vLLM     - Model server (port 8000)"
        echo "  Backend  - API server with tools (ports 8080, 8001)"
        echo "  Frontend - Streamlit UI (port 8501)"
        exit 1
        ;;
esac