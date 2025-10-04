#!/bin/sh

# This entrypoint script simply executes the command passed to it.
# The application will start after this script runs.

echo "Starting application..."
exec "$@"