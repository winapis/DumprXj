#!/bin/bash
# DumprX Enhanced Boot Image Extraction Module
# Improved extraction of vendor_boot, init_boot, boot, recovery with ramdisk analysis

# Source required modules
source "$(dirname "${BASH_SOURCE[0]}")/../core/config.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../messaging/ui.sh"

# Enhanced boot image extraction
extract_boot_images() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    msg_extract "Starting enhanced boot image extraction..."
    
    # Extract different types of boot images
    extract_standard_boot "$firmware_dir" "$output_dir"
    extract_vendor_boot "$firmware_dir" "$output_dir"
    extract_init_boot "$firmware_dir" "$output_dir"
    extract_recovery "$firmware_dir" "$output_dir"
    extract_vendor_kernel_boot "$firmware_dir" "$output_dir"
    
    msg_success "Boot image extraction completed"
}

# Extract standard boot.img
extract_standard_boot() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    while IFS= read -r -d '' boot_file; do
        msg_info "Processing boot image: $(basename "$boot_file")"
        
        # Extract boot image
        local boot_extract_dir="${output_dir}/boot"
        mkdir -p "$boot_extract_dir"
        
        if bash "${UNPACKBOOT}" "$boot_file" "$boot_extract_dir" 2>/dev/null; then
            msg_success "Boot image extracted to: $boot_extract_dir"
            
            # Extract device tree blobs
            extract_dtb_from_boot "$boot_file" "$output_dir"
            
            # Extract and analyze kernel
            analyze_kernel "$boot_extract_dir/kernel" "$output_dir"
            
            # Analyze ramdisk
            analyze_ramdisk "$boot_extract_dir/ramdisk" "$output_dir/boot_ramdisk" "boot"
            
        else
            msg_warning "Failed to extract boot image: $(basename "$boot_file")"
        fi
    done < <(find "$firmware_dir" -name "boot.img" -print0)
}

# Extract vendor_boot.img with enhanced analysis
extract_vendor_boot() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    while IFS= read -r -d '' vendor_boot_file; do
        msg_info "Processing vendor boot image: $(basename "$vendor_boot_file")"
        
        # Extract vendor boot image
        local vendor_boot_extract_dir="${output_dir}/vendor_boot"
        mkdir -p "$vendor_boot_extract_dir"
        
        if bash "${UNPACKBOOT}" "$vendor_boot_file" "$vendor_boot_extract_dir" 2>/dev/null; then
            msg_success "Vendor boot image extracted to: $vendor_boot_extract_dir"
            
            # Extract vendor DTBs
            extract_dtb_from_boot "$vendor_boot_file" "$output_dir" "vendor_"
            
            # Analyze vendor ramdisk
            if [[ -f "$vendor_boot_extract_dir/ramdisk" ]]; then
                analyze_ramdisk "$vendor_boot_extract_dir/ramdisk" "$output_dir/vendor_boot_ramdisk" "vendor_boot"
            fi
            
            # Generate ELF from vendor boot for analysis
            generate_elf_from_boot "$vendor_boot_file" "$output_dir/vendor_bootRE/vendor_boot.elf"
            
        else
            msg_warning "Failed to extract vendor boot image: $(basename "$vendor_boot_file")"
        fi
    done < <(find "$firmware_dir" -name "vendor_boot.img" -print0)
}

# Extract init_boot.img (Android 13+)
extract_init_boot() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    while IFS= read -r -d '' init_boot_file; do
        msg_info "Processing init boot image: $(basename "$init_boot_file")"
        
        # Extract init boot image
        local init_boot_extract_dir="${output_dir}/init_boot"
        mkdir -p "$init_boot_extract_dir"
        
        if bash "${UNPACKBOOT}" "$init_boot_file" "$init_boot_extract_dir" 2>/dev/null; then
            msg_success "Init boot image extracted to: $init_boot_extract_dir"
            
            # Analyze init ramdisk (important for Android 13+)
            if [[ -f "$init_boot_extract_dir/ramdisk" ]]; then
                analyze_ramdisk "$init_boot_extract_dir/ramdisk" "$output_dir/init_boot_ramdisk" "init_boot"
            fi
            
        else
            msg_warning "Failed to extract init boot image: $(basename "$init_boot_file")"
        fi
    done < <(find "$firmware_dir" -name "init_boot.img" -print0)
}

# Extract recovery.img
extract_recovery() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    while IFS= read -r -d '' recovery_file; do
        msg_info "Processing recovery image: $(basename "$recovery_file")"
        
        # Extract recovery image
        local recovery_extract_dir="${output_dir}/recovery"
        mkdir -p "$recovery_extract_dir"
        
        if bash "${UNPACKBOOT}" "$recovery_file" "$recovery_extract_dir" 2>/dev/null; then
            msg_success "Recovery image extracted to: $recovery_extract_dir"
            
            # Analyze recovery ramdisk
            if [[ -f "$recovery_extract_dir/ramdisk" ]]; then
                analyze_ramdisk "$recovery_extract_dir/ramdisk" "$output_dir/recovery_ramdisk" "recovery"
            fi
            
        else
            msg_warning "Failed to extract recovery image: $(basename "$recovery_file")"
        fi
    done < <(find "$firmware_dir" -name "recovery.img" -print0)
}

# Extract vendor_kernel_boot.img (newer devices)
extract_vendor_kernel_boot() {
    local firmware_dir="$1"
    local output_dir="$2"
    
    while IFS= read -r -d '' vendor_kernel_boot_file; do
        msg_info "Processing vendor kernel boot image: $(basename "$vendor_kernel_boot_file")"
        
        # Extract vendor kernel boot image
        local vendor_kernel_boot_extract_dir="${output_dir}/vendor_kernel_boot"
        mkdir -p "$vendor_kernel_boot_extract_dir"
        
        if bash "${UNPACKBOOT}" "$vendor_kernel_boot_file" "$vendor_kernel_boot_extract_dir" 2>/dev/null; then
            msg_success "Vendor kernel boot image extracted to: $vendor_kernel_boot_extract_dir"
            
            # Analyze kernel in vendor kernel boot
            if [[ -f "$vendor_kernel_boot_extract_dir/kernel" ]]; then
                analyze_kernel "$vendor_kernel_boot_extract_dir/kernel" "$output_dir" "vendor_kernel_"
            fi
            
        else
            msg_warning "Failed to extract vendor kernel boot image: $(basename "$vendor_kernel_boot_file")"
        fi
    done < <(find "$firmware_dir" -name "vendor_kernel_boot.img" -print0)
}

# Extract device tree blobs from boot images
extract_dtb_from_boot() {
    local boot_file="$1"
    local output_dir="$2"
    local prefix="${3:-}"
    
    # Create DTB output directories
    local dtb_img_dir="${output_dir}/${prefix}bootimg"
    local dtb_dts_dir="${output_dir}/${prefix}bootdts"
    mkdir -p "$dtb_img_dir" "$dtb_dts_dir"
    
    # Extract DTBs using uvx (if available) or fallback method
    if command -v uvx >/dev/null 2>&1; then
        if uvx -q extract-dtb "$boot_file" -o "$dtb_img_dir" >/dev/null 2>&1; then
            msg_success "DTBs extracted from $(basename "$boot_file")"
            
            # Convert DTBs to DTS
            while IFS= read -r -d '' dtb_file; do
                local dtb_name
                dtb_name=$(basename "$dtb_file")
                local dts_name="${dtb_name/.dtb/.dts}"
                
                if "${DTC}" -q -s -f -I dtb -O dts -o "${dtb_dts_dir}/${dts_name}" "$dtb_file" 2>/dev/null; then
                    msg_info "Converted DTB to DTS: $dts_name"
                fi
            done < <(find "$dtb_img_dir" -name "*.dtb" -print0)
        fi
    else
        msg_warning "uvx not available, skipping DTB extraction"
    fi
}

# Analyze kernel binary
analyze_kernel() {
    local kernel_file="$1"
    local output_dir="$2"
    local prefix="${3:-}"
    
    if [[ ! -f "$kernel_file" ]]; then
        return 1
    fi
    
    msg_info "Analyzing kernel: $(basename "$kernel_file")"
    
    # Create kernel analysis directory
    local kernel_analysis_dir="${output_dir}/${prefix}bootRE"
    mkdir -p "$kernel_analysis_dir"
    
    # Extract kernel config
    if [[ -x "${EXTRACT_IKCONFIG}" ]]; then
        if bash "${EXTRACT_IKCONFIG}" "$kernel_file" > "${kernel_analysis_dir}/ikconfig" 2>/dev/null; then
            if [[ -s "${kernel_analysis_dir}/ikconfig" ]]; then
                msg_success "Kernel config extracted"
                
                # Extract kernel version from config
                local kernel_version
                kernel_version=$(grep "Kernel Configuration" "${kernel_analysis_dir}/ikconfig" | head -1 | awk '{print $3}' 2>/dev/null)
                if [[ -n "$kernel_version" ]]; then
                    echo "$kernel_version" > "${kernel_analysis_dir}/kernel_version"
                    msg_info "Kernel version: $kernel_version"
                fi
            fi
        fi
    fi
    
    # Generate ELF from kernel using vmlinux-to-elf
    if [[ -x "${VMLINUX2ELF}" ]]; then
        local elf_file="${kernel_analysis_dir}/${prefix}boot.elf"
        if python3 "${VMLINUX2ELF}" "$kernel_file" "$elf_file" >/dev/null 2>&1; then
            msg_success "Kernel ELF generated: $(basename "$elf_file")"
        fi
    fi
}

# Enhanced ramdisk analysis with version detection
analyze_ramdisk() {
    local ramdisk_file="$1"
    local output_dir="$2"
    local image_type="$3"
    
    if [[ ! -f "$ramdisk_file" ]]; then
        return 1
    fi
    
    msg_info "Analyzing ramdisk from $image_type"
    
    # Create ramdisk analysis directory
    mkdir -p "$output_dir"
    
    # Detect compression type
    local compression_type
    compression_type=$(detect_ramdisk_compression "$ramdisk_file")
    msg_info "Ramdisk compression: $compression_type"
    
    # Decompress ramdisk
    local decompressed_ramdisk="${output_dir}/ramdisk.cpio"
    if decompress_ramdisk "$ramdisk_file" "$decompressed_ramdisk" "$compression_type"; then
        msg_success "Ramdisk decompressed"
        
        # Extract ramdisk contents
        local ramdisk_contents_dir="${output_dir}/contents"
        mkdir -p "$ramdisk_contents_dir"
        
        cd "$ramdisk_contents_dir" || return 1
        if cpio -idm < "$decompressed_ramdisk" 2>/dev/null; then
            msg_success "Ramdisk contents extracted"
            
            # Analyze ramdisk version and properties
            analyze_ramdisk_version "$ramdisk_contents_dir" "$image_type"
            
            # Extract important files
            extract_ramdisk_info "$ramdisk_contents_dir" "$output_dir"
        fi
        cd - >/dev/null || return 1
    fi
}

# Detect ramdisk compression type
detect_ramdisk_compression() {
    local ramdisk_file="$1"
    
    # Check file type
    local file_info
    file_info=$(file "$ramdisk_file" 2>/dev/null)
    
    case "$file_info" in
        *"gzip compressed"*)
            echo "gzip"
            ;;
        *"LZ4 compressed"*)
            echo "lz4"
            ;;
        *"XZ compressed"*)
            echo "xz"
            ;;
        *"LZMA compressed"*)
            echo "lzma"
            ;;
        *"Zstandard compressed"*)
            echo "zstd"
            ;;
        *"cpio archive"*)
            echo "none"
            ;;
        *)
            # Try to detect by magic bytes
            local magic
            magic=$(xxd -l 4 -p "$ramdisk_file" 2>/dev/null)
            case "$magic" in
                "1f8b"*) echo "gzip" ;;
                "04224d18") echo "lz4" ;;
                "fd377a585a00") echo "xz" ;;
                "5d00"*) echo "lzma" ;;
                "28b52ffd") echo "zstd" ;;
                *) echo "unknown" ;;
            esac
            ;;
    esac
}

# Decompress ramdisk based on compression type
decompress_ramdisk() {
    local input_file="$1"
    local output_file="$2"
    local compression="$3"
    
    case "$compression" in
        "gzip")
            gunzip -c "$input_file" > "$output_file" 2>/dev/null
            ;;
        "lz4")
            lz4 -d "$input_file" "$output_file" 2>/dev/null
            ;;
        "xz")
            xz -dc "$input_file" > "$output_file" 2>/dev/null
            ;;
        "lzma")
            lzma -dc "$input_file" > "$output_file" 2>/dev/null
            ;;
        "zstd")
            zstd -d "$input_file" -o "$output_file" 2>/dev/null
            ;;
        "none")
            cp "$input_file" "$output_file" 2>/dev/null
            ;;
        *)
            msg_warning "Unknown compression type: $compression"
            return 1
            ;;
    esac
}

# Analyze ramdisk version and properties
analyze_ramdisk_version() {
    local ramdisk_contents="$1"
    local image_type="$2"
    
    local version_info="${ramdisk_contents}/version_info.txt"
    echo "=== Ramdisk Analysis for $image_type ===" > "$version_info"
    
    # Detect Android version from various sources
    local android_version="unknown"
    local api_level="unknown"
    
    # Check build.prop files
    for prop_file in default.prop build.prop; do
        if [[ -f "$ramdisk_contents/$prop_file" ]]; then
            local sdk_version
            sdk_version=$(grep "ro.build.version.sdk=" "$ramdisk_contents/$prop_file" 2>/dev/null | cut -d'=' -f2)
            if [[ -n "$sdk_version" ]]; then
                api_level="$sdk_version"
                android_version=$(api_to_android_version "$sdk_version")
                break
            fi
        fi
    done
    
    # Detect ramdisk format version
    local ramdisk_version
    case "$api_level" in
        33|34|35) ramdisk_version="4" ;;
        30|31|32) ramdisk_version="3" ;;
        28|29) ramdisk_version="2" ;;
        *) ramdisk_version="unknown" ;;
    esac
    
    echo "Android Version: $android_version" >> "$version_info"
    echo "API Level: $api_level" >> "$version_info"
    echo "Ramdisk Format Version: $ramdisk_version" >> "$version_info"
    
    msg_success "Ramdisk analysis: Android $android_version (API $api_level), Ramdisk v$ramdisk_version"
}

# Convert API level to Android version
api_to_android_version() {
    local api_level="$1"
    
    case "$api_level" in
        35) echo "15" ;;
        34) echo "14" ;;
        33) echo "13" ;;
        32) echo "12L" ;;
        31) echo "12" ;;
        30) echo "11" ;;
        29) echo "10" ;;
        28) echo "9" ;;
        27) echo "8.1" ;;
        26) echo "8.0" ;;
        25) echo "7.1" ;;
        24) echo "7.0" ;;
        *) echo "Unknown" ;;
    esac
}

# Extract important information from ramdisk
extract_ramdisk_info() {
    local ramdisk_contents="$1"
    local output_dir="$2"
    
    # Extract init scripts
    if [[ -d "$ramdisk_contents/init" ]]; then
        cp -r "$ramdisk_contents/init" "$output_dir/init_scripts" 2>/dev/null
        msg_info "Init scripts extracted"
    fi
    
    # Extract property files
    for prop_file in default.prop build.prop; do
        if [[ -f "$ramdisk_contents/$prop_file" ]]; then
            cp "$ramdisk_contents/$prop_file" "$output_dir/" 2>/dev/null
            msg_info "Property file extracted: $prop_file"
        fi
    done
    
    # Extract sepolicy
    if [[ -f "$ramdisk_contents/sepolicy" ]]; then
        cp "$ramdisk_contents/sepolicy" "$output_dir/" 2>/dev/null
        msg_info "SEPolicy extracted"
    fi
}

# Generate ELF from boot image
generate_elf_from_boot() {
    local boot_file="$1"
    local elf_output="$2"
    
    mkdir -p "$(dirname "$elf_output")"
    
    if [[ -x "${VMLINUX2ELF}" ]]; then
        if python3 "${VMLINUX2ELF}" "$boot_file" "$elf_output" >/dev/null 2>&1; then
            msg_success "ELF generated: $(basename "$elf_output")"
            return 0
        fi
    fi
    
    return 1
}

# Export functions
export -f extract_boot_images extract_standard_boot extract_vendor_boot extract_init_boot
export -f extract_recovery extract_vendor_kernel_boot extract_dtb_from_boot analyze_kernel
export -f analyze_ramdisk detect_ramdisk_compression decompress_ramdisk analyze_ramdisk_version
export -f api_to_android_version extract_ramdisk_info generate_elf_from_boot