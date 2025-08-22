#!/bin/bash
# DumprX Standalone Telegram Bot
# Can be run independently to provide Telegram bot functionality

# Set up script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Source required modules
source "${PROJECT_DIR}/lib/core/config.sh"
source "${PROJECT_DIR}/lib/messaging/ui.sh"
source "${PROJECT_DIR}/lib/messaging/telegram.sh"

# Bot configuration
BOT_MODE="${1:-polling}"  # polling or webhook
WEBHOOK_URL="${2:-}"      # webhook URL if webhook mode

# Initialize configuration
init_config
init_telegram_config

# Check if Telegram token is configured
if [[ -z "$TG_TOKEN" ]]; then
    msg_error "Telegram token not configured!"
    msg_info "Please create a .tg_token file with your bot token"
    exit 1
fi

# Banner for bot startup
show_bot_banner() {
    echo -e "${C_CYAN}"
    cat << 'EOF'
	╔══════════════════════════════════════════╗
	║           DumprX Telegram Bot            ║
	║        Advanced Firmware Extractor      ║
	╚══════════════════════════════════════════╝
EOF
    echo -e "${C_CLEAR}"
}

# Enhanced bot command handlers
handle_telegram_command() {
    local command="$1"
    local chat_id="$2"
    local message_id="$3"
    shift 3
    local args=("$@")
    
    # Log command
    msg_info "Received command: $command from chat: $chat_id"
    
    case "$command" in
        "/start")
            send_welcome_message "$chat_id"
            ;;
        "/help")
            send_help_message "$chat_id"
            ;;
        "/status")
            send_status_message "$chat_id"
            ;;
        "/extract")
            handle_extract_command "$chat_id" "${args[@]}"
            ;;
        "/cancel")
            handle_cancel_command "$chat_id"
            ;;
        "/queue")
            handle_queue_command "$chat_id"
            ;;
        "/supported")
            send_supported_formats "$chat_id"
            ;;
        "/examples")
            send_examples "$chat_id"
            ;;
        *)
            # Check if message contains a URL
            if [[ "$command" =~ https?:// ]]; then
                handle_extract_command "$chat_id" "$command"
            else
                send_unknown_command "$chat_id" "$command"
            fi
            ;;
    esac
}

# Enhanced message handlers
send_welcome_message() {
    local chat_id="$1"
    
    local message="🔥 <b>Welcome to DumprX Bot!</b>\n\n"
    message+="I'm an advanced firmware extraction bot that can help you extract and analyze Android firmware files.\n\n"
    message+="<b>🚀 Quick Start:</b>\n"
    message+="• Send me a firmware URL to start extraction\n"
    message+="• Use /help to see all available commands\n"
    message+="• Use /supported to see supported formats\n\n"
    message+="<b>💫 Features:</b>\n"
    message+="• Support for 15+ firmware formats\n"
    message+="• Automatic manufacturer detection\n"
    message+="• Advanced boot image analysis\n"
    message+="• Multiple download services support\n"
    message+="• Real-time progress updates\n\n"
    message+="<i>Ready to extract some firmware? 📱</i>"
    
    send_bot_message "$chat_id" "$message"
}

send_help_message() {
    local chat_id="$1"
    
    local message="<b>🤖 DumprX Bot Commands</b>\n\n"
    message+="<b>📱 Extraction Commands:</b>\n"
    message+="/extract &lt;url&gt; - Extract firmware from URL\n"
    message+="/cancel - Cancel current extraction\n"
    message+="/queue - Show extraction queue\n\n"
    message+="<b>ℹ️ Information Commands:</b>\n"
    message+="/status - Check bot status\n"
    message+="/supported - Show supported formats\n"
    message+="/examples - Show usage examples\n"
    message+="/help - Show this help\n\n"
    message+="<b>💡 Tips:</b>\n"
    message+="• You can also send URLs directly without /extract\n"
    message+="• Wrap URLs in quotes if they contain special characters\n"
    message+="• Large files may take several minutes to process\n\n"
    message+="<i>Need more help? Contact the developer!</i>"
    
    send_bot_message "$chat_id" "$message"
}

send_status_message() {
    local chat_id="$1"
    
    local uptime
    uptime=$(uptime -p 2>/dev/null || echo "unknown")
    
    local disk_usage
    disk_usage=$(df -h "${PROJECT_DIR}" 2>/dev/null | awk 'NR==2 {print $5}' || echo "unknown")
    
    local memory_usage
    memory_usage=$(free | awk 'NR==2{printf "%.0f%%", $3*100/$2}' 2>/dev/null || echo "unknown")
    
    local message="<b>🤖 DumprX Bot Status</b>\n\n"
    message+="<b>🟢 Status:</b> Online and Ready\n"
    message+="<b>⏱ Uptime:</b> $uptime\n"
    message+="<b>💾 Disk Usage:</b> $disk_usage\n"
    message+="<b>🧠 Memory Usage:</b> $memory_usage\n"
    message+="<b>🔧 Version:</b> DumprX v2.0\n\n"
    message+="<b>📊 Capabilities:</b>\n"
    message+="• ✅ Firmware extraction\n"
    message+="• ✅ Manufacturer detection\n"
    message+="• ✅ Boot image analysis\n"
    message+="• ✅ Partition extraction\n"
    message+="• ✅ Multi-service downloads\n\n"
    message+="<i>All systems operational! 🚀</i>"
    
    send_bot_message "$chat_id" "$message"
}

send_supported_formats() {
    local chat_id="$1"
    
    local message="<b>📦 Supported Firmware Formats</b>\n\n"
    message+="<b>📱 Android Firmware:</b>\n"
    message+="• ZIP, RAR, 7Z, TAR archives\n"
    message+="• Samsung TAR.MD5 files\n"
    message+="• OZIP (OnePlus/OPPO encrypted)\n"
    message+="• OFP (OPPO firmware packages)\n"
    message+="• OPS (OnePlus firmware)\n"
    message+="• KDZ (LG firmware)\n"
    message+="• RUU (HTC ROM update)\n"
    message+="• NB0 (Nokia firmware)\n"
    message+="• PAC (Spreadtrum firmware)\n"
    message+="• UPDATE.APP (Huawei)\n\n"
    message+="<b>🌐 Download Sources:</b>\n"
    message+="• Direct download links\n"
    message+="• Mega.nz\n"
    message+="• MediaFire\n"
    message+="• Google Drive\n"
    message+="• OneDrive\n"
    message+="• AndroidFileHost\n"
    message+="• Dropbox\n"
    message+="• GitHub/GitLab releases\n\n"
    message+="<i>More formats added regularly! 🔄</i>"
    
    send_bot_message "$chat_id" "$message"
}

send_examples() {
    local chat_id="$1"
    
    local message="<b>💡 Usage Examples</b>\n\n"
    message+="<b>🔗 Direct Download:</b>\n"
    message+="<code>/extract https://example.com/firmware.zip</code>\n\n"
    message+="<b>☁️ Cloud Storage:</b>\n"
    message+="<code>/extract https://mega.nz/file/ABC123</code>\n"
    message+="<code>/extract https://drive.google.com/file/d/XYZ</code>\n\n"
    message+="<b>📱 Specific Formats:</b>\n"
    message+="<code>/extract https://example.com/samsung.tar.md5</code>\n"
    message+="<code>/extract https://example.com/oneplus.ozip</code>\n"
    message+="<code>/extract https://example.com/lg.kdz</code>\n\n"
    message+="<b>⚡ Quick Send:</b>\n"
    message+="You can also send URLs directly:\n"
    message+="<code>https://example.com/firmware.zip</code>\n\n"
    message+="<b>🔍 What happens next:</b>\n"
    message+="1. Bot downloads the firmware\n"
    message+="2. Detects manufacturer and format\n"
    message+="3. Extracts all partitions\n"
    message+="4. Analyzes boot images\n"
    message+="5. Uploads to Git repository\n"
    message+="6. Sends you the results link\n\n"
    message+="<i>Simple as that! 🎉</i>"
    
    send_bot_message "$chat_id" "$message"
}

send_unknown_command() {
    local chat_id="$1"
    local command="$2"
    
    local message="❓ <b>Unknown command:</b> <code>$command</code>\n\n"
    message+="<b>💡 Did you mean:</b>\n"
    message+="• /help - Show available commands\n"
    message+="• /extract &lt;url&gt; - Extract firmware\n"
    message+="• /status - Check bot status\n\n"
    message+="Or simply send me a firmware URL directly! 🔗"
    
    send_bot_message "$chat_id" "$message"
}

# Enhanced extraction handling with queue support
declare -A EXTRACTION_QUEUE
declare -g CURRENT_EXTRACTION=""

handle_extract_command() {
    local chat_id="$1"
    shift
    local args=("$@")
    
    if [[ ${#args[@]} -eq 0 ]]; then
        local message="❌ <b>Error:</b> No firmware URL provided.\n\n"
        message+="<b>Usage:</b>\n"
        message+="<code>/extract https://example.com/firmware.zip</code>\n\n"
        message+="<b>💡 Tip:</b> You can also send URLs directly without /extract"
        send_bot_message "$chat_id" "$message"
        return
    fi
    
    local firmware_url="${args[0]}"
    
    # Validate URL
    if ! [[ "$firmware_url" =~ ^https?:// ]]; then
        send_bot_message "$chat_id" "❌ Invalid URL format. Please provide a valid HTTP/HTTPS URL."
        return
    fi
    
    # Check if extraction is already in progress
    if [[ -n "$CURRENT_EXTRACTION" ]]; then
        # Add to queue
        local queue_id="${chat_id}_$(date +%s)"
        EXTRACTION_QUEUE["$queue_id"]="$chat_id:$firmware_url"
        
        local message="⏳ <b>Added to queue</b>\n\n"
        message+="Another extraction is currently in progress.\n"
        message+="Your request has been queued.\n\n"
        message+="<b>Queue position:</b> ${#EXTRACTION_QUEUE[@]}\n"
        message+="<b>URL:</b> <code>$firmware_url</code>\n\n"
        message+="Use /queue to check queue status."
        
        send_bot_message "$chat_id" "$message"
        return
    fi
    
    # Start extraction
    start_extraction "$chat_id" "$firmware_url"
}

start_extraction() {
    local chat_id="$1"
    local firmware_url="$2"
    
    CURRENT_EXTRACTION="$chat_id"
    
    local message="🔄 <b>Starting firmware extraction...</b>\n\n"
    message+="<b>📱 URL:</b> <code>$firmware_url</code>\n\n"
    message+="<b>⏱ This may take a while depending on:</b>\n"
    message+="• File size and download speed\n"
    message+="• Firmware complexity\n"
    message+="• Current server load\n\n"
    message+="<i>I'll keep you updated on the progress! 📊</i>"
    
    send_bot_message "$chat_id" "$message"
    
    # Start extraction in background
    {
        # Change to project directory
        cd "$PROJECT_DIR" || exit 1
        
        # Run the extraction
        bash "./dumper_v2.sh" "$firmware_url" 2>&1
        local exit_code=$?
        
        # Clear current extraction
        CURRENT_EXTRACTION=""
        
        # Send completion message
        if [[ $exit_code -eq 0 ]]; then
            local success_message="✅ <b>Extraction completed successfully!</b>\n\n"
            success_message+="<b>🎉 Your firmware has been processed and uploaded.</b>\n\n"
            success_message+="Check the channel for the download link! 📂"
            send_bot_message "$chat_id" "$success_message"
        else
            local error_message="❌ <b>Extraction failed</b>\n\n"
            error_message+="<b>Possible reasons:</b>\n"
            error_message+="• Invalid or broken firmware file\n"
            error_message+="• Unsupported format\n"
            error_message+="• Network connectivity issues\n"
            error_message+="• Server temporary issues\n\n"
            error_message+="<i>Please try again or contact support if the issue persists.</i>"
            send_bot_message "$chat_id" "$error_message"
        fi
        
        # Process next item in queue
        process_next_in_queue
        
    } &
    
    # Store the background process PID for potential cancellation
    local extraction_pid=$!
    echo "$extraction_pid" > "/tmp/dumprx_extraction_${chat_id}.pid"
}

handle_cancel_command() {
    local chat_id="$1"
    
    if [[ "$CURRENT_EXTRACTION" == "$chat_id" ]]; then
        # Cancel current extraction
        local pid_file="/tmp/dumprx_extraction_${chat_id}.pid"
        if [[ -f "$pid_file" ]]; then
            local pid
            pid=$(cat "$pid_file")
            if kill "$pid" 2>/dev/null; then
                send_bot_message "$chat_id" "✅ <b>Extraction cancelled successfully.</b>"
                CURRENT_EXTRACTION=""
                rm -f "$pid_file"
                process_next_in_queue
            else
                send_bot_message "$chat_id" "⚠️ <b>Could not cancel extraction.</b>\n\nIt may have already completed."
            fi
        else
            send_bot_message "$chat_id" "❓ <b>No active extraction found to cancel.</b>"
        fi
    else
        # Remove from queue if present
        local removed=false
        for queue_id in "${!EXTRACTION_QUEUE[@]}"; do
            if [[ "${EXTRACTION_QUEUE[$queue_id]}" =~ ^$chat_id: ]]; then
                unset EXTRACTION_QUEUE["$queue_id"]
                removed=true
                break
            fi
        done
        
        if [[ "$removed" == "true" ]]; then
            send_bot_message "$chat_id" "✅ <b>Removed from extraction queue.</b>"
        else
            send_bot_message "$chat_id" "❓ <b>No extraction found to cancel.</b>"
        fi
    fi
}

handle_queue_command() {
    local chat_id="$1"
    
    local message="📋 <b>Extraction Queue Status</b>\n\n"
    
    if [[ -n "$CURRENT_EXTRACTION" ]]; then
        message+="<b>🔄 Currently Processing:</b> Chat $CURRENT_EXTRACTION\n\n"
    fi
    
    if [[ ${#EXTRACTION_QUEUE[@]} -eq 0 ]]; then
        message+="<b>📭 Queue is empty</b>\n\n"
        message+="<i>Send a firmware URL to start extraction!</i>"
    else
        message+="<b>⏳ Queued Extractions:</b> ${#EXTRACTION_QUEUE[@]}\n\n"
        
        local position=1
        for queue_id in "${!EXTRACTION_QUEUE[@]}"; do
            local queue_item="${EXTRACTION_QUEUE[$queue_id]}"
            local queue_chat_id="${queue_item%%:*}"
            local queue_url="${queue_item#*:}"
            
            if [[ "$queue_chat_id" == "$chat_id" ]]; then
                message+="<b>$position.</b> 👤 <b>Your request</b>\n"
                message+="    <code>$(echo "$queue_url" | cut -c1-50)...</code>\n\n"
            else
                message+="<b>$position.</b> Other user\n\n"
            fi
            
            ((position++))
        done
    fi
    
    send_bot_message "$chat_id" "$message"
}

process_next_in_queue() {
    if [[ ${#EXTRACTION_QUEUE[@]} -gt 0 ]]; then
        # Get next item from queue
        local next_queue_id
        next_queue_id=$(printf '%s\n' "${!EXTRACTION_QUEUE[@]}" | sort | head -1)
        
        local queue_item="${EXTRACTION_QUEUE[$next_queue_id]}"
        local next_chat_id="${queue_item%%:*}"
        local next_url="${queue_item#*:}"
        
        # Remove from queue
        unset EXTRACTION_QUEUE["$next_queue_id"]
        
        # Start next extraction
        start_extraction "$next_chat_id" "$next_url"
    fi
}

# Main bot startup
main() {
    show_bot_banner
    
    msg_info "Starting DumprX Telegram Bot..."
    msg_info "Mode: $BOT_MODE"
    msg_info "Token: ${TG_TOKEN:0:10}..."
    
    if [[ "$BOT_MODE" == "webhook" ]]; then
        if [[ -z "$WEBHOOK_URL" ]]; then
            msg_error "Webhook URL required for webhook mode"
            exit 1
        fi
        
        msg_info "Setting up webhook: $WEBHOOK_URL"
        start_telegram_bot "$WEBHOOK_URL"
    else
        msg_info "Starting in polling mode..."
        start_telegram_bot
    fi
}

# Trap signals for graceful shutdown
trap 'msg_info "Shutting down bot..."; exit 0' SIGINT SIGTERM

# Run main function
main "$@"