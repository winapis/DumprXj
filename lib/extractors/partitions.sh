#!/bin/bash
# DumprX Enhanced Partition Detection Module
# Advanced partition detection and handling

# Source required modules
source "$(dirname "${BASH_SOURCE[0]}")/../core/config.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../messaging/ui.sh"

# Enhanced partition detection
detect_partitions() {
    local firmware_path="$1"
    local detected_partitions=()
    
    msg_search "Scanning for partitions..."
    
    # Check for common partition files
    while IFS= read -r -d '' file; do
        local basename_file
        basename_file=$(basename "$file")
        
        # Remove common suffixes to get partition name
        local partition_name
        partition_name="${basename_file%.*}"
        partition_name="${partition_name%-p*}"
        partition_name="${partition_name%-sign*}"
        partition_name="${partition_name%-verified*}"
        
        # Check if it's a known partition
        if [[ " $PARTITIONS " =~ " $partition_name " ]]; then
            detected_partitions+=("$partition_name:$file")
            msg_success "Found partition: $partition_name"
        fi
    done < <(find "$firmware_path" -type f \( -name "*.img" -o -name "*.bin" -o -name "*.sin" \) -print0)
    
    # Detect super partition and its sub-partitions
    detect_super_partitions "$firmware_path" detected_partitions
    
    # Detect vendor boot and related partitions
    detect_boot_partitions "$firmware_path" detected_partitions
    
    # Output results
    if [[ ${#detected_partitions[@]} -gt 0 ]]; then
        msg_success "Detected ${#detected_partitions[@]} partitions"
        printf '%s\n' "${detected_partitions[@]}"
    else
        msg_warning "No partitions detected"
        return 1
    fi
}

# Detect super partition and its contents
detect_super_partitions() {
    local firmware_path="$1"
    local -n partition_array=$2
    
    # Look for super.img files
    while IFS= read -r -d '' super_file; do
        msg_info "Analyzing super partition: $(basename "$super_file")"
        
        # Try to get partition info from super.img
        if command -v lpunpack >/dev/null 2>&1; then
            local temp_dir
            temp_dir=$(mktemp -d)
            
            # Extract super partition info
            if lpunpack -l "$super_file" 2>/dev/null | grep -E "^Partition" > "$temp_dir/partitions.txt"; then
                while read -r line; do
                    if [[ "$line" =~ Partition\ ([^:]+): ]]; then
                        local part_name="${BASH_REMATCH[1]}"
                        partition_array+=("$part_name:$super_file")
                        msg_success "Found super sub-partition: $part_name"
                    fi
                done < "$temp_dir/partitions.txt"
            fi
            
            rm -rf "$temp_dir"
        fi
    done < <(find "$firmware_path" -type f -name "*super*.img" -print0)
}

# Detect boot-related partitions with enhanced ramdisk version detection
detect_boot_partitions() {
    local firmware_path="$1"
    local -n partition_array=$2
    
    # Boot partition variants
    local boot_partitions=("boot" "vendor_boot" "init_boot" "recovery" "vendor_kernel_boot")
    
    for boot_type in "${boot_partitions[@]}"; do
        while IFS= read -r -d '' boot_file; do
            msg_info "Analyzing boot partition: $(basename "$boot_file")"
            partition_array+=("$boot_type:$boot_file")
            
            # Detect ramdisk version in boot images
            detect_ramdisk_version "$boot_file"
            
        done < <(find "$firmware_path" -type f -name "*${boot_type}*.img" -print0)
    done
}

# Enhanced ramdisk version detection (supports versions 2, 3, 4)
detect_ramdisk_version() {
    local boot_image="$1"
    local temp_dir
    temp_dir=$(mktemp -d)
    
    # Try to unpack boot image and analyze ramdisk
    if bash "${UNPACKBOOT}" "$boot_image" "$temp_dir" >/dev/null 2>&1; then
        local ramdisk_file="$temp_dir/ramdisk"
        
        if [[ -f "$ramdisk_file" ]]; then
            # Try to decompress and analyze ramdisk
            local ramdisk_extracted="$temp_dir/ramdisk_extracted"
            mkdir -p "$ramdisk_extracted"
            
            # Detect compression type and decompress
            local file_type
            file_type=$(file "$ramdisk_file" 2>/dev/null)
            
            case "$file_type" in
                *"gzip compressed"*)
                    gunzip -c "$ramdisk_file" > "$temp_dir/ramdisk.cpio" 2>/dev/null
                    ;;
                *"LZ4 compressed"*)
                    lz4 -d "$ramdisk_file" "$temp_dir/ramdisk.cpio" 2>/dev/null
                    ;;
                *"XZ compressed"*)
                    xz -dc "$ramdisk_file" > "$temp_dir/ramdisk.cpio" 2>/dev/null
                    ;;
                *"LZMA compressed"*)
                    lzma -dc "$ramdisk_file" > "$temp_dir/ramdisk.cpio" 2>/dev/null
                    ;;
                *"cpio archive"*)
                    cp "$ramdisk_file" "$temp_dir/ramdisk.cpio"
                    ;;
            esac
            
            # Extract cpio if we have it
            if [[ -f "$temp_dir/ramdisk.cpio" ]]; then
                cd "$ramdisk_extracted" || return
                cpio -idm < "$temp_dir/ramdisk.cpio" 2>/dev/null
                cd - >/dev/null || return
                
                # Detect ramdisk version from various indicators
                detect_ramdisk_version_from_files "$ramdisk_extracted" "$(basename "$boot_image")"
            fi
        fi
    fi
    
    rm -rf "$temp_dir"
}

# Detect ramdisk version from extracted files
detect_ramdisk_version_from_files() {
    local ramdisk_dir="$1"
    local image_name="$2"
    local version="unknown"
    
    # Check for version indicators
    if [[ -f "$ramdisk_dir/init" ]]; then
        # Check init binary for version info
        if strings "$ramdisk_dir/init" 2>/dev/null | grep -q "Android.*13\|API.*33"; then
            version="4"
        elif strings "$ramdisk_dir/init" 2>/dev/null | grep -q "Android.*1[12]\|API.*3[012]"; then
            version="3"
        elif strings "$ramdisk_dir/init" 2>/dev/null | grep -q "Android.*[89]10\|API.*2[789]"; then
            version="2"
        fi
    fi
    
    # Check for property files
    if [[ -f "$ramdisk_dir/default.prop" ]]; then
        if grep -q "ro.build.version.sdk=3[3-9]" "$ramdisk_dir/default.prop" 2>/dev/null; then
            version="4"
        elif grep -q "ro.build.version.sdk=3[0-2]" "$ramdisk_dir/default.prop" 2>/dev/null; then
            version="3"
        elif grep -q "ro.build.version.sdk=2[789]" "$ramdisk_dir/default.prop" 2>/dev/null; then
            version="2"
        fi
    fi
    
    # Check for sepolicy version
    if [[ -f "$ramdisk_dir/sepolicy" ]]; then
        local sepolicy_version
        sepolicy_version=$(strings "$ramdisk_dir/sepolicy" 2>/dev/null | grep -o "3[0-9]\.[0-9]" | head -1)
        if [[ -n "$sepolicy_version" ]]; then
            case "${sepolicy_version%%.*}" in
                33|34|35) version="4" ;;
                30|31|32) version="3" ;;
                28|29) version="2" ;;
            esac
        fi
    fi
    
    # Report findings
    if [[ "$version" != "unknown" ]]; then
        msg_success "Ramdisk version detected in $image_name: v$version"
    else
        msg_warning "Could not determine ramdisk version for $image_name"
    fi
    
    echo "$version"
}

# Enhanced partition type detection
detect_partition_type() {
    local partition_file="$1"
    local file_type
    
    # Use file command to detect type
    file_type=$(file "$partition_file" 2>/dev/null)
    
    case "$file_type" in
        *"Android sparse image"*)
            echo "sparse"
            ;;
        *"Linux rev 1.0 ext4 filesystem"*)
            echo "ext4"
            ;;
        *"Linux rev 1.0 ext2 filesystem"*)
            echo "ext2"
            ;;
        *"Linux rev 1.0 ext3 filesystem"*)
            echo "ext3"
            ;;
        *"F2FS filesystem"*)
            echo "f2fs"
            ;;
        *"Android bootimg"*)
            echo "bootimg"
            ;;
        *"data"* | *"Non-ISO extended-ASCII"*)
            # Try to detect based on magic bytes
            local magic
            magic=$(xxd -l 8 -p "$partition_file" 2>/dev/null)
            case "$magic" in
                "3aff26ed"*) echo "sparse" ;;
                "53ef"*) echo "ext4" ;;
                "414e44524f4944"*) echo "bootimg" ;;
                *) echo "raw" ;;
            esac
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Validate partition integrity
validate_partition() {
    local partition_file="$1"
    local partition_type="$2"
    
    case "$partition_type" in
        "sparse")
            # Validate sparse image
            if command -v simg2img >/dev/null 2>&1; then
                simg2img -s "$partition_file" >/dev/null 2>&1
            else
                return 1
            fi
            ;;
        "ext4"|"ext3"|"ext2")
            # Basic file existence check for now
            [[ -f "$partition_file" ]]
            ;;
        "bootimg")
            # Check for Android boot image magic
            local magic
            magic=$(xxd -l 8 -p "$partition_file" 2>/dev/null)
            [[ "$magic" == "414e44524f4944"* ]]
            ;;
        *)
            # Basic file existence check
            [[ -f "$partition_file" ]]
            ;;
    esac
}

# Export functions
export -f detect_partitions detect_super_partitions detect_boot_partitions
export -f detect_ramdisk_version detect_ramdisk_version_from_files
export -f detect_partition_type validate_partition