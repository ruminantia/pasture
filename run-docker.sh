#!/bin/bash

# =============================================================================
# Ruminantia Pasture - Docker Container Management Script
#
# This script provides a convenient command-line interface for managing the
# multi-source content scraper using Docker. It handles configuration validation,
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
    # 2. Verifies that at least one pasture is configured
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
        echo "1. Edit config.ini to configure which pastures to monitor"
        echo "2. Add sections for each content source you want to scrape"
        echo ""
        echo "Example config.ini structure:"
        echo "[global]"
        echo "remove_tags = script, style, noscript, iframe"
        echo ""
        echo "[worldnews]"
        echo "type = reddit"
        echo "url = https://www.reddit.com/r/worldnews.json"
        echo "blacklist = politics, election"
        echo ""
        echo "[hackernews_top]"
        echo "type = hackernews"
        echo "blacklist = cryptocurrency, bitcoin"
        echo ""
        exit 1
    fi

    # Verify that config.ini has at least one pasture configured (not just [global])
    if ! grep -q "^\[.*\]" config.ini | grep -v "\[global\]" | head -1; then
        print_warning "config.ini exists but may not have any pastures configured"
        echo "Add sections for content sources you want to scrape, for example:"
        echo ""
        echo "[worldnews]"
        echo "type = reddit"
        echo "url = https://www.reddit.com/r/worldnews.json"
        echo "blacklist = politics, election"
        echo ""
        echo "[hackernews_top]"
        echo "type = hackernews"
        echo "blacklist = cryptocurrency, bitcoin"
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
    # Start the Pasture scraper in detached mode (background).
    #
    # This runs the container as a background service, freeing up the terminal.
    # The scraper will run continuously with scheduled scraping intervals.
    print_status "Starting Ruminantia Pasture scraper in detached mode..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose up -d
    else
        docker run -d \
            --name pasture-scraper \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            pasture
    fi

    print_status "Scraper started successfully!"
    echo "To view logs: ./run-docker.sh logs"
    echo "To stop the scraper: ./run-docker.sh stop"
    echo ""
    echo "The scraper will run continuously and scrape content from configured pastures."
    echo "Check config.ini for interval settings per pasture."
}

stop_scraper() {
    # Stop the running scraper container and clean up resources.
    #
    # This stops the container and removes it.
    # All data in mounted volumes (output files) is preserved.
    print_status "Stopping Ruminantia Pasture scraper..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose down
    else
        docker stop pasture-scraper 2>/dev/null || true
        docker rm pasture-scraper 2>/dev/null || true
    fi

    print_status "Scraper stopped successfully!"
}

restart_scraper() {
    # Restart the scraper container with current configuration.
    #
    # Useful for applying configuration changes or running another scrape.
    # The container is stopped and started with the same settings.
    print_status "Restarting Ruminantia Pasture scraper..."

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
        # For Docker Compose, show logs in follow mode
        docker compose logs -f
    else
        docker logs -f pasture-scraper
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
        docker build -t pasture .
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
        docker ps -a --filter "name=pasture-scraper"
    fi
}

start_attached() {
    # Start the scraper in attached mode for debugging.
    #
    # Runs the container in the foreground, showing real-time output.
    # The terminal will be occupied until the scraper is stopped with Ctrl+C.
    check_config_file
    print_status "Starting Ruminantia Pasture scraper in attached mode..."
    print_warning "Press Ctrl+C to stop the scraper"
    print_warning "Terminal will be occupied until scraper is stopped"

    if [ "$USE_COMPOSE" = true ]; then
        docker compose up
    else
        docker run -it \
            --rm \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            pasture
    fi
}

run_once() {
    # Run the scraper once and exit (attached mode).
    #
    # This runs a single scrape session and then exits.
    # Useful for manual execution or testing.
    check_config_file
    print_status "Running Ruminantia Pasture scraper (single run)..."

    if [ "$USE_COMPOSE" = true ]; then
        docker compose run --rm -T pasture-scraper
    else
        docker run --rm \
            -v "$(pwd)/config.ini:/app/config.ini" \
            -v "$(pwd)/output:/app/output" \
            pasture
    fi
}

show_help() {
    # Display comprehensive help information for the management script.
    #
    # Provides usage instructions, available commands, and examples.
    # This is the default help message shown when users need assistance.
    echo "Ruminantia Pasture - Multi-Source Content Scraper Management Script"
    echo "=================================================================="
    echo ""
    echo "A convenient interface for managing the multi-source content scraper."
    echo "Supports Reddit, HackerNews, and other content sources (pastures)."
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
    echo "  - The scraper runs continuously with scheduled scraping intervals"
    echo "  - Supports multiple content sources (pastures): Reddit, HackerNews, etc."
    echo "  - Use 'start' for background execution (recommended)"
    echo "  - Use 'run' for single execution (testing/debugging)"
    echo "  - Data is preserved in mounted volumes across runs"
    echo "  - Configuration is loaded from config.ini"
    echo "  - Set 'interval' in config.ini sections to control scraping frequency (minutes)"
    echo ""
    if [ "$USE_COMPOSE" = true ]; then
        echo "Mode: Docker Compose (docker-compose.yml detected)"
    else
        echo "Mode: Direct Docker commands"
    fi
    echo ""
    echo "Examples:"
    echo "  ./run-docker.sh           # Run scraper once (testing)"
    echo "  ./run-docker.sh start     # Start in background (recommended)"
    echo "  ./run-docker.sh logs      # View real-time logs"
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
        # Default behavior: run once and exit (for testing)
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
