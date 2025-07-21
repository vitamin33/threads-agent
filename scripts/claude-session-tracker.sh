#!/usr/bin/env bash
# ================================================================
#  CLAUDE SESSION TRACKER - Auto-commit for each session
# ================================================================

set -euo pipefail

# Configuration
readonly SESSION_LOG=".claude-sessions/session_log.json"
readonly SESSION_DIR=".claude-sessions"

# Create session directory if it doesn't exist
mkdir -p "$SESSION_DIR"

# Function to generate session ID
generate_session_id() {
    echo "claude-$(date +%Y%m%d-%H%M%S)-$(head -c 4 /dev/urandom | base64 | tr -d '/' | tr -d '+' | tr -d '=')"
}

# Function to start session tracking
start_session() {
    local session_id=$(generate_session_id)
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Log session start
    local session_data=$(jq -n \
        --arg id "$session_id" \
        --arg timestamp "$timestamp" \
        --arg status "active" \
        '{
            session_id: $id,
            start_time: $timestamp,
            status: $status,
            files_modified: [],
            commands_run: [],
            summary: ""
        }')
    
    # Save session data
    echo "$session_data" > "$SESSION_DIR/current_session.json"
    
    # Add to session log
    if [[ -f "$SESSION_LOG" ]]; then
        jq --argjson session "$session_data" '.sessions += [$session]' "$SESSION_LOG" > "$SESSION_LOG.tmp" && mv "$SESSION_LOG.tmp" "$SESSION_LOG"
    else
        echo '{"sessions": []}' | jq --argjson session "$session_data" '.sessions += [$session]' > "$SESSION_LOG"
    fi
    
    echo "$session_id"
}

# Function to track file modifications
track_modification() {
    local file_path="$1"
    local action="${2:-modified}"
    
    if [[ -f "$SESSION_DIR/current_session.json" ]]; then
        local modification=$(jq -n \
            --arg file "$file_path" \
            --arg action "$action" \
            --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            '{
                file: $file,
                action: $action,
                timestamp: $timestamp
            }')
        
        jq --argjson mod "$modification" '.files_modified += [$mod]' "$SESSION_DIR/current_session.json" > "$SESSION_DIR/current_session.json.tmp" && mv "$SESSION_DIR/current_session.json.tmp" "$SESSION_DIR/current_session.json"
    fi
}

# Function to track command execution
track_command() {
    local command="$1"
    local exit_code="${2:-0}"
    
    if [[ -f "$SESSION_DIR/current_session.json" ]]; then
        local cmd_data=$(jq -n \
            --arg cmd "$command" \
            --arg code "$exit_code" \
            --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            '{
                command: $cmd,
                exit_code: ($code | tonumber),
                timestamp: $timestamp
            }')
        
        jq --argjson cmd "$cmd_data" '.commands_run += [$cmd]' "$SESSION_DIR/current_session.json" > "$SESSION_DIR/current_session.json.tmp" && mv "$SESSION_DIR/current_session.json.tmp" "$SESSION_DIR/current_session.json"
    fi
}

# Function to end session and commit
end_session() {
    local summary="${1:-Claude Code session completed}"
    
    if [[ ! -f "$SESSION_DIR/current_session.json" ]]; then
        echo "No active session found"
        return 1
    fi
    
    local session_data=$(cat "$SESSION_DIR/current_session.json")
    local session_id=$(echo "$session_data" | jq -r '.session_id')
    local end_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Update session with end time and summary
    local final_session=$(echo "$session_data" | jq \
        --arg end_time "$end_time" \
        --arg summary "$summary" \
        --arg status "completed" \
        '.end_time = $end_time | .summary = $summary | .status = $status')
    
    # Save final session data
    echo "$final_session" > "$SESSION_DIR/session_${session_id}.json"
    
    # Update session log
    jq --arg id "$session_id" --argjson updated "$final_session" \
        '.sessions = (.sessions | map(if .session_id == $id then $updated else . end))' \
        "$SESSION_LOG" > "$SESSION_LOG.tmp" && mv "$SESSION_LOG.tmp" "$SESSION_LOG"
    
    # Get modified files for commit
    local modified_files=$(echo "$final_session" | jq -r '.files_modified[].file' | sort -u)
    
    if [[ -n "$modified_files" ]]; then
        # Stage all modified files
        echo "$modified_files" | xargs git add
        
        # Create commit message
        local commit_msg="Claude Code Session: $session_id

$summary

Modified files:
$(echo "$modified_files" | sed 's/^/- /')

Commands executed:
$(echo "$final_session" | jq -r '.commands_run[].command' | head -10 | sed 's/^/- /')

🤖 Auto-generated commit by Claude Code Session Tracker"
        
        # Commit changes
        git commit -m "$commit_msg" || echo "No changes to commit"
        
        echo "✅ Session $session_id committed with $(echo "$modified_files" | wc -l) files"
    else
        echo "ℹ️ Session $session_id completed with no file changes"
    fi
    
    # Clean up current session
    rm -f "$SESSION_DIR/current_session.json"
}

# Function to get current session info
session_status() {
    if [[ -f "$SESSION_DIR/current_session.json" ]]; then
        local session_data=$(cat "$SESSION_DIR/current_session.json")
        local session_id=$(echo "$session_data" | jq -r '.session_id')
        local start_time=$(echo "$session_data" | jq -r '.start_time')
        local files_count=$(echo "$session_data" | jq -r '.files_modified | length')
        
        echo "Active Session: $session_id"
        echo "Started: $start_time"
        echo "Files modified: $files_count"
        
        if (( files_count > 0 )); then
            echo "Modified files:"
            echo "$session_data" | jq -r '.files_modified[].file' | sed 's/^/  - /'
        fi
    else
        echo "No active session"
    fi
}

# Function to list recent sessions
list_sessions() {
    local limit="${1:-10}"
    
    if [[ -f "$SESSION_LOG" ]]; then
        echo "Recent Claude Code Sessions:"
        jq -r --arg limit "$limit" \
            '.sessions | sort_by(.start_time) | reverse | .[:($limit | tonumber)] | 
            .[] | "[\(.start_time | split("T")[0])] \(.session_id) - \(.summary // "No summary")"' \
            "$SESSION_LOG"
    else
        echo "No sessions found"
    fi
}

# Main command handler
case "${1:-help}" in
    "start")
        session_id=$(start_session)
        echo "Started Claude session: $session_id"
        ;;
    "track-file")
        track_modification "$2" "${3:-modified}"
        ;;
    "track-command")
        track_command "$2" "${3:-0}"
        ;;
    "end")
        end_session "${2:-Claude Code session completed}"
        ;;
    "status")
        session_status
        ;;
    "list")
        list_sessions "${2:-10}"
        ;;
    "help"|*)
        echo "Claude Session Tracker"
        echo ""
        echo "Usage:"
        echo "  $0 start                    - Start new session"
        echo "  $0 track-file FILE [ACTION] - Track file modification"
        echo "  $0 track-command CMD [CODE] - Track command execution"
        echo "  $0 end [SUMMARY]           - End session and commit"
        echo "  $0 status                  - Show current session"
        echo "  $0 list [LIMIT]           - List recent sessions"
        ;;
esac