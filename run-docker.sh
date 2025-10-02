#!/bin/bash

# =============================================================================
# Ruminantia Graze - Docker Container Management Script
#
# This script provides a convenient command-line interface for managing the
# Reddit/web content scraper using Docker. It handles configuration validation,
# container lifecycle management, and user-friendly error messages.
# =============================================================================

# Exit immediately if any command fails
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# COLOR DEFINITIONS FOR USER-FRIENDLY OUTPUT
# =============================================================================
RED='\033[0;31m'      # Error messages
GREEN='\033[0;32m'    # Success messages
YELLOW='\033[1;33m'   # Warning messages
NC='\033[0m'          # No Color (reset)

# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================

# Print informational status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Print warning messages for non-critical issues
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Print error messages and exit if necessary
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# DOCKER COMPOSE DETECTION
# =============================================================================

# Check if docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    USE_COMPOSE=true
    print_status "Using Docker Compose configuration"
else
    USE_COMPOSE=false
    print_warning "docker-compose.yml not found, using direct Docker commands"
fi

# =============================================================================
# CONFIGURATION VALIDATION FUNCTIONS
# =============================================================================

check_config_file() {
    # Validate that the config.ini file exists and contains basic configuration.
    #
    # This function:
    # 1. Checks for the existence of the config.ini file
    # 2. Verifies that at least one subreddit is configured
    # 3. Creates necessary output directories if they don't exist
    # 4. Provides helpful guidance if configuration is missing
    #
    # Exits with error code 1 if config.ini file is missing.
    if [ ! -f config.ini ]; then
        print_error "config.ini file not found!"
        echo ""
        echo "Configuration file is required for the scraper to function."
        echo ""
        echo "Setup instructions:"
        echo "1. Edit config.ini to configure which subreddits to monitor"
        echo "2. Add sections for each subreddit you want to scrape"
        echo ""
        echo "Example config.ini structure:"
        echo "[global]"
        echo "remove_tags = script, style, noscript, iframe"
        echo ""
        echo "[worldnews]"
        echo "url = https://www.reddit.com/r/worldnews.json"
        echo "blacklist = politics, election"
        echo ""
        echo "[technology]"
        echo "url = https://www.reddit.com/r/technology.json"
        echo "blacklist = AI, cryptocurrency"
        exit 1
    fi

    # Verify that config.ini has at least one subreddit configured (not just [global])
    if ! grep -q "^\[.*\]" config.ini | grep -v "\[global\]" | head -1; then
        print_warning "config.ini exists but may not have any subreddits configured"
        echo "Add sections for subreddits you want to scrape, for example:"
        echo ""
        echo "[worldnews]"
        echo "url = https://www.reddit.com/r/worldnews.json"
        echo "blacklist = politics, election"
        echo ""
        echo "See README.md for complete configuration options."
    fi

    # Ensure necessary output directories exist
    if [ ! -d "output" ]; then
        print_warning "Creating missing output directory"
        mkdir -p output
    fi
}

# =============================================================================
# CONTAINER MANAGEMENT FUNCTIONS
# =============================================================================

start_scraper() {
    # Start the Graze scraper in detached mode (background).
    #
    # This runs the container as a background service, freeing up the terminal.
    # The scraper will run once and exit unless configured otherwise.
    print_status "Starting Ruminantia Graze scraper in detached mode..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose up -d
    else
        docker run -d \
            --name graze-scraper \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            graze
    fi

    print_status "Scraper started successfully!"
    echo "To view logs: ./run-docker.sh logs"
    echo "To stop the scraper: ./run-docker.sh stop"
}

stop_scraper() {
    # Stop the running scraper container and clean up resources.
    #
    # This stops the container and removes it.
    # All data in mounted volumes (output files) is preserved.
    print_status "Stopping Ruminantia Graze scraper..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose down
    else
        docker stop graze-scraper 2>/dev/null || true
        docker rm graze-scraper 2>/dev/null || true
    fi

    print_status "Scraper stopped successfully!"
}

restart_scraper() {
    # Restart the scraper container with current configuration.
    #
    # Useful for applying configuration changes or running another scrape.
    # The container is stopped and started with the same settings.
    print_status "Restarting Ruminantia Graze scraper..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose restart
    else
        stop_scraper
        start_scraper
    fi

    print_status "Scraper restarted successfully!"
}

view_logs() {
    # Display real-time container logs in follow mode.
    #
    # Shows the scraper's output stream. Useful for debugging and monitoring.
    # Press Ctrl+C to exit log viewing mode.
    print_status "Showing scraper logs (Ctrl+C to exit)..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose logs -f
    else
        docker logs -f graze-scraper
    fi
}

build_image() {
    # Build the Docker image from scratch.
    #
    # Useful when Dockerfile changes are made or to ensure a clean build.
    print_status "Building Docker image..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose build
    else
        docker build -t graze .
    fi

    print_status "Image built successfully!"
}

show_status() {
    # Display the current status of Docker containers.
    #
    # Shows running/stopped status, container names, and other details.
    # Useful for verifying the scraper's operational state.
    print_status "Container status:"

    if [ "$USE_COMPOSE" = true ]; then
        docker compose ps
    else
        docker ps -a --filter "name=graze-scraper"
    fi
}

start_attached() {
    # Start the scraper in attached mode for debugging.
    #
    # Runs the container in the foreground, showing real-time output.
    # The terminal will be occupied until the scraper completes or is stopped.
    check_config_file
    print_status "Starting Ruminantia Graze scraper in attached mode..."
    print_warning "Terminal will be occupied until scraper completes"

    if [ "$USE_COMPOSE" = true ]; then
        docker compose up
    else
        docker run -it \
            --rm \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            graze
    fi
}

run_once() {
    # Run the scraper once and exit (attached mode).
    #
    # This is the default behavior - run a single scrape session.
    # Useful for scheduled runs or manual execution.
    check_config_file
    print_status "Running Ruminantia Graze scraper (single run)..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose run --rm -T graze-scraper
    else
        docker run --rm \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            graze
    fi
}

show_help() {
    # Display comprehensive help information for the management script.
    #
    # Provides usage instructions, available commands, and examples.
    # This is the default help message shown when users need assistance.
    echo "Ruminantia Graze - Content Scraper Management Script"
    echo "===================================================="
    echo ""
    echo "A convenient interface for managing the Reddit/web content scraper."
    echo ""
    echo "Usage: ./run-docker.sh [command]"
    echo ""
    echo "Available Commands:"
    echo "  run       - Run the scraper once and exit (default)"
    echo "  start     - Start the scraper in detached mode"
    echo "  stop      - Stop the running scraper container"
    echo "  restart   - Restart the scraper with current configuration"
    echo "  logs      - View real-time scraper logs"
    echo "  build     - Build the Docker image"
    echo "  status    - Show container status information"
    echo "  attach    - Start in attached mode for debugging"
    echo "  help      - Display this help message"
    echo ""
    echo "Default Behavior:"
    echo "  If no command is provided, the scraper runs once and exits."
    echo ""
    echo "Operational Notes:"
    echo "  - The scraper typically runs once and exits (not a long-running service)"
    echo "  - Use 'start' for background execution"
    echo "  - Use 'run' or no command for single execution"
    echo "  - Data is preserved in mounted volumes across runs"
    echo "  - Configuration is loaded from config.ini"
    echo ""
    if [ "$USE_COMPOSE" = true ]; then
        echo "Mode: Docker Compose (docker-compose.yml detected)"
    else
        echo "Mode: Direct Docker commands"
    fi
    echo ""
    echo "Examples:"
    echo "  ./run-docker.sh           # Run scraper once (default)"
    echo "  ./run-docker.sh start     # Start in background"
    echo "  ./run-docker.sh logs      # View logs of running container"
    echo "  ./run-docker.sh stop      # Stop background container"
    echo "  ./run-docker.sh build     # Rebuild Docker image"
    echo ""
    echo "For more information, see the project README.md file."
}

# =============================================================================
# MAIN SCRIPT LOGIC - COMMAND DISPATCHER
# =============================================================================

case "${1:-}" in
    "start")
        # Start the scraper in detached mode (background)
        check_config_file
        build_image
        start_scraper
        ;;
    "stop")
        # Stop the running scraper container
        stop_scraper
        ;;
    "restart")
        # Restart the scraper with current configuration
        check_config_file
        restart_scraper
        ;;
    "logs")
        # Display real-time container logs
        view_logs
        ;;
    "build")
        # Build the Docker image
        build_image
        ;;
    "status")
        # Show container status information
        show_status
        ;;
    "attach")
        # Start scraper in attached mode for debugging
        start_attached
        ;;
    "run")
        # Run scraper once (attached mode)
        run_once
        ;;
    "help"|"-h"|"--help")
        # Display comprehensive help information
        show_help
        ;;
    "")
        # Default behavior: run once and exit
        check_config_file
        build_image
        run_once
        ;;
    *)
        # Handle unknown commands with helpful error message
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
