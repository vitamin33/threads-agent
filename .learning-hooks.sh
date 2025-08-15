#!/bin/bash
# Auto-track commands in learning system

original_command="$1"
shift
args="$@"

start_time=$(date +%s.%N)
$original_command $args
exit_code=$?
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc -l)

# Track in learning system
if [[ -f "scripts/learning-system.sh" ]]; then
    ./scripts/learning-system.sh track "$original_command $args" "$exit_code" "$duration" "agent:${AGENT_ID:-unknown}" >/dev/null 2>&1 &
fi

exit $exit_code
