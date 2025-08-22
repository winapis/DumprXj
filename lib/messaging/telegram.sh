#!/bin/bash
# DumprX Enhanced Telegram Bot and Notification System
# Improved messaging and bot functionality

# Source required modules
source "$(dirname "${BASH_SOURCE[0]}")/../messaging/ui.sh"

# Telegram configuration
declare -g TG_TOKEN=""
declare -g CHAT_ID=""
declare -g GITLAB_HOST=""

# Initialize Telegram configuration
init_telegram_config() {
    # Load Telegram token
    if [[ -s "${PROJECT_DIR}/.tg_token" ]]; then
        TG_TOKEN=$(< "${PROJECT_DIR}/.tg_token")
    fi
    
    # Load chat ID
    if [[ -s "${PROJECT_DIR}/.tg_chat" ]]; then
        CHAT_ID=$(< "${PROJECT_DIR}/.tg_chat")
    else
        CHAT_ID="@DumprXDumps"  # Default channel
    fi
    
    # Load GitLab host if needed
    if [[ -s "${PROJECT_DIR}/.gitlab_instance" ]]; then
        GITLAB_HOST=$(< "${PROJECT_DIR}/.gitlab_instance")
    else
        GITLAB_HOST="gitlab.com"
    fi
}

# Enhanced Telegram message formatting
format_telegram_message() {
    local brand="$1"
    local device="$2"
    local platform="$3"
    local android_version="$4"
    local kernel_version="$5"
    local fingerprint="$6"
    local repo="$7"
    local branch="$8"
    local git_org="$9"
    local provider="${10:-github}"
    
    local message=""
    local repo_url=""
    
    # Determine repository URL based on provider
    if [[ "$provider" == "gitlab" ]]; then
        repo_url="https://${GITLAB_HOST}/${git_org}/${repo}/-/tree/${branch}/"
    else
        repo_url="https://github.com/${git_org}/${repo}/tree/${branch}/"
    fi
    
    # Create enhanced message with emojis and formatting
    message="<b>🔥 New Firmware Dump Available!</b>\n\n"
    message+="<b>📱 Device Information</b>\n"
    message+="├ <b>Brand:</b> ${brand}\n"
    message+="├ <b>Device:</b> ${device}\n"
    message+="├ <b>Platform:</b> ${platform}\n"
    message+="└ <b>Android:</b> ${android_version}\n\n"
    
    if [[ -n "$kernel_version" ]]; then
        message+="<b>🔧 Kernel Version:</b> ${kernel_version}\n\n"
    fi
    
    message+="<b>🔍 Build Information</b>\n"
    message+="└ <b>Fingerprint:</b> <code>${fingerprint}</code>\n\n"
    
    message+="<b>📂 Repository</b>\n"
    message+="└ <a href=\"${repo_url}\">Browse Files</a>\n\n"
    
    message+="<b>⚡ Extracted with DumprX v2.0</b>\n"
    message+="<i>Advanced firmware extraction toolkit</i>"
    
    echo "$message"
}

# Send enhanced Telegram notification
send_telegram_notification() {
    local brand="$1"
    local device="$2" 
    local platform="$3"
    local android_version="$4"
    local kernel_version="$5"
    local fingerprint="$6"
    local repo="$7"
    local branch="$8"
    local git_org="$9"
    local provider="${10:-github}"
    
    # Check if Telegram is configured
    if [[ -z "$TG_TOKEN" ]]; then
        msg_warning "Telegram token not configured, skipping notification"
        return 1
    fi
    
    init_telegram_config
    
    msg_progress "Preparing Telegram notification..."
    
    # Format the message
    local message
    message=$(format_telegram_message "$brand" "$device" "$platform" "$android_version" "$kernel_version" "$fingerprint" "$repo" "$branch" "$git_org" "$provider")
    
    # Send notification
    msg_progress "Sending Telegram notification..."
    
    local response
    response=$(curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${CHAT_ID}\",
            \"text\": \"${message}\",
            \"parse_mode\": \"HTML\",
            \"disable_web_page_preview\": true,
            \"disable_notification\": false
        }")
    
    # Check if message was sent successfully
    if echo "$response" | grep -q '"ok":true'; then
        msg_success "Telegram notification sent successfully"
        return 0
    else
        msg_error "Failed to send Telegram notification"
        if [[ "${DEBUG:-0}" == "1" ]]; then
            echo "Response: $response" >&2
        fi
        return 1
    fi
}

# Send progress update to Telegram
send_progress_update() {
    local stage="$1"
    local progress="$2"
    local details="$3"
    
    if [[ -z "$TG_TOKEN" ]]; then
        return 1
    fi
    
    local message="<b>🔄 DumprX Progress Update</b>\n\n"
    message+="<b>Stage:</b> ${stage}\n"
    message+="<b>Progress:</b> ${progress}%\n"
    
    if [[ -n "$details" ]]; then
        message+="<b>Details:</b> ${details}\n"
    fi
    
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${CHAT_ID}\",
            \"text\": \"${message}\",
            \"parse_mode\": \"HTML\",
            \"disable_web_page_preview\": true,
            \"disable_notification\": true
        }" >/dev/null
}

# Send error notification to Telegram
send_error_notification() {
    local error_stage="$1"
    local error_message="$2"
    local firmware_url="$3"
    
    if [[ -z "$TG_TOKEN" ]]; then
        return 1
    fi
    
    local message="<b>❌ DumprX Extraction Failed</b>\n\n"
    message+="<b>Stage:</b> ${error_stage}\n"
    message+="<b>Error:</b> <code>${error_message}</code>\n"
    
    if [[ -n "$firmware_url" ]]; then
        message+="<b>Firmware URL:</b> ${firmware_url}\n"
    fi
    
    message+="\n<i>Please check the logs for more details.</i>"
    
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${CHAT_ID}\",
            \"text\": \"${message}\",
            \"parse_mode\": \"HTML\",
            \"disable_web_page_preview\": true,
            \"disable_notification\": false
        }" >/dev/null
}

# Telegram bot command handlers
handle_telegram_command() {
    local command="$1"
    local chat_id="$2"
    local message_id="$3"
    shift 3
    local args=("$@")
    
    case "$command" in
        "/start")
            send_bot_message "$chat_id" "🔥 Welcome to DumprX Bot!\n\nI can help you extract firmware. Use /help for available commands."
            ;;
        "/help")
            local help_text="<b>🤖 DumprX Bot Commands</b>\n\n"
            help_text+="/start - Start the bot\n"
            help_text+="/help - Show this help\n"
            help_text+="/status - Check bot status\n"
            help_text+="/extract <url> - Extract firmware from URL\n"
            help_text+="/cancel - Cancel current operation\n\n"
            help_text+="<i>Send me a firmware URL to start extraction!</i>"
            send_bot_message "$chat_id" "$help_text"
            ;;
        "/status")
            send_bot_message "$chat_id" "🟢 DumprX Bot is running!\n\nReady to extract firmware."
            ;;
        "/extract")
            if [[ ${#args[@]} -eq 0 ]]; then
                send_bot_message "$chat_id" "❌ Please provide a firmware URL.\n\nExample: /extract https://example.com/firmware.zip"
            else
                handle_extract_command "$chat_id" "${args[0]}"
            fi
            ;;
        "/cancel")
            send_bot_message "$chat_id" "✅ Current operation cancelled."
            ;;
        *)
            # Check if message contains a URL
            if [[ "$command" =~ https?:// ]]; then
                handle_extract_command "$chat_id" "$command"
            else
                send_bot_message "$chat_id" "❓ Unknown command. Use /help for available commands."
            fi
            ;;
    esac
}

# Handle extract command
handle_extract_command() {
    local chat_id="$1"
    local firmware_url="$2"
    
    send_bot_message "$chat_id" "🔄 Starting firmware extraction...\n\nURL: ${firmware_url}\n\nThis may take a while depending on the file size."
    
    # Start extraction in background
    {
        # Run the actual extraction
        bash "${PROJECT_DIR}/dumper.sh" "$firmware_url" 2>&1
        local exit_code=$?
        
        if [[ $exit_code -eq 0 ]]; then
            send_bot_message "$chat_id" "✅ Firmware extraction completed successfully!"
        else
            send_bot_message "$chat_id" "❌ Firmware extraction failed. Please check the provided URL."
        fi
    } &
}

# Send message to specific chat
send_bot_message() {
    local chat_id="$1"
    local message="$2"
    
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${chat_id}\",
            \"text\": \"${message}\",
            \"parse_mode\": \"HTML\",
            \"disable_web_page_preview\": true
        }" >/dev/null
}

# Telegram bot webhook handler
start_telegram_bot() {
    local webhook_url="$1"
    
    if [[ -z "$TG_TOKEN" ]]; then
        msg_error "Telegram token not configured"
        return 1
    fi
    
    msg_info "Starting Telegram bot..."
    
    # Set webhook if URL provided
    if [[ -n "$webhook_url" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/setWebhook" \
            -H "Content-Type: application/json" \
            -d "{\"url\": \"${webhook_url}\"}" >/dev/null
        msg_success "Webhook set to: $webhook_url"
    fi
    
    # Start polling mode if no webhook
    if [[ -z "$webhook_url" ]]; then
        start_telegram_polling
    fi
}

# Telegram polling mode
start_telegram_polling() {
    local offset=0
    
    msg_info "Starting Telegram polling mode..."
    
    while true; do
        local updates
        updates=$(curl -s -X GET "https://api.telegram.org/bot${TG_TOKEN}/getUpdates?offset=${offset}&timeout=30")
        
        if echo "$updates" | grep -q '"ok":true'; then
            # Process updates
            local update_ids
            update_ids=$(echo "$updates" | jq -r '.result[].update_id' 2>/dev/null)
            
            while read -r update_id; do
                if [[ -n "$update_id" && "$update_id" != "null" ]]; then
                    process_telegram_update "$updates" "$update_id"
                    offset=$((update_id + 1))
                fi
            done <<< "$update_ids"
        fi
        
        sleep 1
    done
}

# Process individual Telegram update
process_telegram_update() {
    local updates="$1"
    local update_id="$2"
    
    # Extract message data
    local chat_id
    local message_text
    local message_id
    
    chat_id=$(echo "$updates" | jq -r ".result[] | select(.update_id == $update_id) | .message.chat.id" 2>/dev/null)
    message_text=$(echo "$updates" | jq -r ".result[] | select(.update_id == $update_id) | .message.text" 2>/dev/null)
    message_id=$(echo "$updates" | jq -r ".result[] | select(.update_id == $update_id) | .message.message_id" 2>/dev/null)
    
    if [[ -n "$chat_id" && -n "$message_text" && "$message_text" != "null" ]]; then
        # Parse command and arguments
        local command
        local args=()
        
        read -ra message_parts <<< "$message_text"
        command="${message_parts[0]}"
        args=("${message_parts[@]:1}")
        
        # Handle the command
        handle_telegram_command "$command" "$chat_id" "$message_id" "${args[@]}"
    fi
}

# Export functions
export -f init_telegram_config format_telegram_message send_telegram_notification
export -f send_progress_update send_error_notification handle_telegram_command
export -f start_telegram_bot send_bot_message