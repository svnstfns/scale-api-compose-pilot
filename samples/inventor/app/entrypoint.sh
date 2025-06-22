#!/bin/bash

# Print banner
echo "======================================"
echo "VideoInventory Processing Application"
echo "======================================"
echo "Starting services..."

# Set up logging
LOG_DIR="/app/logs"
mkdir -p $LOG_DIR
DEBUG_LOG="$LOG_DIR/entrypoint-debug.log"

# Debug function
debug_log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEBUG_LOG"
}

debug_log "Starting entrypoint script"

# List environment variables (without secrets)
debug_log "Environment variables:"
env | grep -v "PASS\|KEY\|SECRET\|TOKEN" | tee -a "$DEBUG_LOG"

# Check Python and dependencies
debug_log "Python version:"
python3 --version | tee -a "$DEBUG_LOG"

debug_log "Installed Python packages:"
pip list | tee -a "$DEBUG_LOG"

# Verify DATA_DIRS environment variable
if [ -z "$DATA_DIRS" ]; then
  debug_log "ERROR: DATA_DIRS environment variable is not set!"
  exit 1
fi

# Check mount directories
debug_log "Checking mount directories:"
IFS=',' read -ra DIR_ARRAY <<< "$DATA_DIRS"
for dir in "${DIR_ARRAY[@]}"; do
  dir=$(echo "$dir" | xargs)  # Trim whitespace
  if [ -d "$dir" ]; then
    debug_log "Directory exists: $dir"
    ls -la "$dir" | head -n 5 | tee -a "$DEBUG_LOG"
  else
    debug_log "Directory MISSING: $dir"
    # Create directory for testing if needed
    if [ "$DEBUG" = "1" ]; then
      debug_log "Creating missing directory (debug mode): $dir"
      mkdir -p "$dir"
      chmod 755 "$dir"
    fi
  fi
done

# Start the FastAPI web service in background
debug_log "Starting FastAPI web monitoring service..."
cd /app && python3 -m app.webservice > "$LOG_DIR/webservice.log" 2>&1 &
WEBSERVICE_PID=$!
debug_log "Web service started with PID: $WEBSERVICE_PID"

# Give the web service a moment to start
sleep 5

# Function to check if web service is up
check_webservice() {
    if ! kill -0 $WEBSERVICE_PID 2>/dev/null; then
        debug_log "Web service process is not running!"
        return 1
    fi

    # Try to access the health endpoint
    if curl -s http://localhost:80/api/health >/dev/null; then
        debug_log "Web service is responding to requests"
        return 0
    else
        # Try a simple connection to port 80
        if nc -z -w2 localhost 80; then
            debug_log "Web service seems to be running but health endpoint not responding"
            return 0
        else
            debug_log "Web service is not responding to requests"
            return 1
        fi
    fi
}

# Check web service health
if ! check_webservice; then
    debug_log "Web service failed to start properly. Checking logs:"
    tail -n 20 "$LOG_DIR/webservice.log" | tee -a "$DEBUG_LOG"
    # We continue anyway as the main processing is more important
fi

# Run the main application with output to a log file and increased verbosity
debug_log "Starting main VideoInventory application..."
cd /app && python3 -m app.main --threads 4 --debug > "$LOG_DIR/main-output.log" 2>&1 &
MAIN_PID=$!
debug_log "Main application started with PID: $MAIN_PID"

# Monitor the main application while keeping the container alive
while kill -0 $MAIN_PID 2>/dev/null; do
    debug_log "Main application is running (PID: $MAIN_PID)"
    sleep 60
done

MAIN_EXIT_CODE=$?
debug_log "Main application exited with code: $MAIN_EXIT_CODE"

# Dump the tail of the main output log for debugging
debug_log "Last output from main application:"
tail -n 50 "$LOG_DIR/main-output.log" | tee -a "$DEBUG_LOG"

# Check if the web service is still running
if kill -0 $WEBSERVICE_PID 2>/dev/null; then
    debug_log "Web service is still running, keeping container alive"
    # Keep container running for the web interface
    debug_log "Main application completed. Keeping container alive for web interface."

    # Use tail -f on logs to keep container running while showing logs
    tail -f "$LOG_DIR/main-output.log" "$LOG_DIR/webservice.log" "$DEBUG_LOG"
else
    debug_log "Web service has stopped, container will exit"
    exit $MAIN_EXIT_CODE
fi