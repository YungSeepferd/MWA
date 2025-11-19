#!/bin/bash
# MAFA Docker Development Environment Script
# Manages the development Docker containers

set -e

# Configuration
COMMAND=${1:-"help"}
SERVICE=${2:-"all"}
ENV_FILE=${ENV_FILE:-".env.dev"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

print_subsection() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
}

# Function to check Docker and Docker Compose
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to create environment file
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_info "Creating development environment file: $ENV_FILE"
        cat > "$ENV_FILE" << EOF
# MAFA Development Environment Variables
MAFA_ENV=development
MAFA_LOG_LEVEL=DEBUG
CONFIG_PATH=config.json
PYTHONPATH=/app

# Database
DATABASE_URL=sqlite:///data/contacts.db

# Redis (optional)
REDIS_URL=redis://mafa-redis:6379/0

# Discord Webhook (replace with actual webhook for testing)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Development settings
DEBUG=true
RELOAD=true
EOF
        print_success "Environment file created: $ENV_FILE"
        print_warning "Please edit $ENV_FILE with your actual settings"
    else
        print_info "Environment file already exists: $ENV_FILE"
    fi
}

# Function to start development environment
start_dev() {
    print_section "Starting MAFA Development Environment"
    
    create_env_file
    
    print_info "Building and starting development containers..."
    
    # Use docker-compose.dev.yml for development
    if docker compose -f docker-compose.dev.yml up -d; then
        print_success "Development environment started successfully"
        
        print_subsection "Service URLs"
        echo "🌐 FastAPI Dashboard: http://localhost:8000"
        echo "🌐 API Documentation: http://localhost:8000/docs"
        echo "🌐 Streamlit Dashboard: http://localhost:3001"
        echo "🌐 MCP Shim: http://localhost:3000"
        echo "🔴 Redis: localhost:6379"
        echo ""
        
        print_subsection "Container Status"
        docker compose -f docker-compose.dev.yml ps
    else
        print_error "Failed to start development environment"
        exit 1
    fi
}

# Function to stop development environment
stop_dev() {
    print_section "Stopping MAFA Development Environment"
    
    if docker compose -f docker-compose.dev.yml down; then
        print_success "Development environment stopped"
    else
        print_error "Failed to stop development environment"
        exit 1
    fi
}

# Function to restart development environment
restart_dev() {
    print_section "Restarting MAFA Development Environment"
    
    stop_dev
    sleep 2
    start_dev
}

# Function to show logs
logs_dev() {
    local service="$1"
    
    if [ -z "$service" ]; then
        print_info "Showing logs for all services..."
        docker compose -f docker-compose.dev.yml logs -f
    else
        print_info "Showing logs for service: $service"
        docker compose -f docker-compose.dev.yml logs -f "$service"
    fi
}

# Function to execute command in container
exec_dev() {
    local service="$1"
    shift
    local command="$@"
    
    if [ -z "$service" ]; then
        print_error "Service name is required"
        echo "Usage: $0 exec <service> <command>"
        exit 1
    fi
    
    print_info "Executing command in $service: $command"
    docker compose -f docker-compose.dev.yml exec "$service" $command
}

# Function to run tests in container
test_dev() {
    print_section "Running Tests in Development Environment"
    
    print_info "Running test suite..."
    if docker compose -f docker-compose.dev.yml run --rm mafa-tests; then
        print_success "Tests completed successfully"
        print_info "Test results available in test-results/ directory"
    else
        print_error "Tests failed"
        exit 1
    fi
}

# Function to run linting in container
lint_dev() {
    print_section "Running Code Quality Checks"
    
    print_info "Running linting and formatting checks..."
    if docker compose -f docker-compose.dev.yml run --rm mafa-lint; then
        print_success "Code quality checks passed"
    else
        print_error "Code quality checks failed"
        exit 1
    fi
}

# Function to run health checks
health_dev() {
    print_section "Running Health Checks"
    
    print_info "Running comprehensive health checks..."
    if docker compose -f docker-compose.dev.yml run --rm mafa-health-check; then
        print_success "Health checks completed"
        print_info "Health check reports available in health-checks/ directory"
    else
        print_error "Health checks failed"
        exit 1
    fi
}

# Function to build containers
build_dev() {
    print_section "Building Development Containers"
    
    print_info "Building all development containers..."
    if docker compose -f docker-compose.dev.yml build; then
        print_success "Containers built successfully"
    else
        print_error "Failed to build containers"
        exit 1
    fi
}

# Function to clean up
clean_dev() {
    print_section "Cleaning Development Environment"
    
    print_info "Stopping and removing containers..."
    docker compose -f docker-compose.dev.yml down -v
    
    print_info "Removing unused images..."
    docker image prune -f
    
    print_info "Cleaning up volumes..."
    docker volume prune -f
    
    print_success "Development environment cleaned"
}

# Function to show status
status_dev() {
    print_section "Development Environment Status"
    
    print_subsection "Container Status"
    docker compose -f docker-compose.dev.yml ps
    
    print_subsection "Resource Usage"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to show help
show_help() {
    echo "MAFA Docker Development Environment Script"
    echo ""
    echo "Usage: $0 <command> [service] [options]"
    echo ""
    echo "Commands:"
    echo "  start [service]     Start development environment (all services)"
    echo "  stop [service]      Stop development environment"
    echo "  restart [service]   Restart development environment"
    echo "  logs [service]      Show logs for service (or all if no service specified)"
    echo "  exec <service> <cmd> Execute command in container"
    echo "  test                Run tests in development environment"
    echo "  lint                Run code quality checks"
    echo "  health              Run health checks"
    echo "  build               Build development containers"
    echo "  clean               Clean up containers and images"
    echo "  status              Show environment status"
    echo "  help                Show this help message"
    echo ""
    echo "Services:"
    echo "  mafa-dev             Main MAFA application (port 8000)"
    echo "  mafa-api             FastAPI server (port 8001)"
    echo "  mafa-scheduler       Background scheduler"
    echo "  mafa-dashboard       Streamlit dashboard (port 3001)"
    echo "  mafa-mcp-shim        MCP shim server (port 3000)"
    echo "  mafa-db              SQLite database"
    echo "  mafa-redis           Redis cache"
    echo ""
    echo "Examples:"
    echo "  $0 start             # Start all services"
    echo "  $0 start mafa-dev     # Start only main application"
    echo "  $0 logs mafa-dev      # Show logs for main application"
    echo "  $0 exec mafa-dev bash # Open shell in main container"
    echo "  $0 test               # Run all tests"
    echo "  $0 lint               # Run code quality checks"
    echo ""
}

# Main execution
main() {
    local command="$1"
    
    if [ -z "$command" ]; then
        show_help
        exit 0
    fi
    
    # Check Docker availability
    check_docker
    
    case "$command" in
        "start")
            start_dev
            ;;
        "stop")
            stop_dev
            ;;
        "restart")
            restart_dev
            ;;
        "logs")
            logs_dev "$2"
            ;;
        "exec")
            exec_dev "$2" "${@:3}"
            ;;
        "test")
            test_dev
            ;;
        "lint")
            lint_dev
            ;;
        "health")
            health_dev
            ;;
        "build")
            build_dev
            ;;
        "clean")
            clean_dev
            ;;
        "status")
            status_dev
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"