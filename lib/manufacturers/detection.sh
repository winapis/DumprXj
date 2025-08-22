#!/bin/bash
# DumprX Enhanced Manufacturer Detection Module
# Improved firmware type detection by manufacturer

# Source required modules
source "$(dirname "${BASH_SOURCE[0]}")/../messaging/ui.sh"

# Manufacturer detection patterns
declare -A MANUFACTURER_PATTERNS=(
    ["samsung"]="AP_|BL_|CP_|CSC_|HOME_CSC_|USERDATA_|PIT|samsung|SM-|GT-|SCH-|SGH-|SPH-"
    ["xiaomi"]="miui|xiaomi|redmi|poco|MI |HM |pocophone"
    ["huawei"]="huawei|honor|UPDATE.APP|HWOTA|P30|P40|Mate|nova"
    ["oppo"]="oppo|oneplus|realme|\.ozip|\.ofp|\.ops|ColorOS|OxygenOS|realmeUI"
    ["vivo"]="vivo|iqoo|funtouch|PD.*\.img"
    ["lg"]="\.kdz|\.dz|lg-|LM-|VS995|H870"
    ["htc"]="ruu.*\.exe|htc|HTC|\.ruuuuuu"
    ["sony"]="xperia|sony|\.ftf|\.sin|E65.*|F83.*|G81.*"
    ["motorola"]="motorola|moto|XT[0-9]|sparsechunk"
    ["nokia"]="nokia|\.nb0|HMD|TA-[0-9]"
    ["asus"]="asus|zenfone|rog|WW_|TW_|CN_|IN_"
    ["lenovo"]="lenovo|\.pac|QFIL|QDL"
    ["google"]="pixel|nexus|sailfish|taimen|crosshatch|flame|coral"
)

# Manufacturer-specific file patterns
declare -A MANUFACTURER_FILES=(
    ["samsung"]="*.pit *.tar.md5 AP_*.tar.md5 BL_*.tar.md5 CP_*.tar.md5 CSC_*.tar.md5"
    ["xiaomi"]="*.tgz *.zip *miui* *xiaomi* images/*.img"
    ["huawei"]="UPDATE.APP *.zip *HWOTA* update_*.zip"
    ["oppo"]="*.ozip *.ofp *.ops *.zip *ColorOS* *OxygenOS*"
    ["lg"]="*.kdz *.dz *.zip"
    ["htc"]="RUU_*.exe *.zip rom.zip"
    ["sony"]="*.ftf *.sin kernel.sin system.sin"
    ["motorola"]="*.zip *sparsechunk* *.xml.p7s"
    ["nokia"]="*.nb0 *.zip *TA-*"
    ["asus"]="*.zip *.raw UL-ASUS_*"
    ["lenovo"]="*.pac *.zip *.mbn rawprogram*.xml"
    ["google"]="*.zip image-*.zip *.img"
)

# Enhanced manufacturer detection
detect_manufacturer() {
    local firmware_path="$1"
    local detected_manufacturer=""
    local confidence=0
    local detection_details=()
    
    msg_search "Analyzing firmware for manufacturer signatures..."
    
    # Check files and directories for manufacturer patterns
    while IFS= read -r -d '' item; do
        local item_name
        item_name=$(basename "$item")
        local item_lower
        item_lower=$(echo "$item_name" | tr '[:upper:]' '[:lower:]')
        
        # Check against manufacturer patterns
        for manufacturer in "${!MANUFACTURER_PATTERNS[@]}"; do
            local patterns="${MANUFACTURER_PATTERNS[$manufacturer]}"
            IFS='|' read -ra pattern_array <<< "$patterns"
            
            for pattern in "${pattern_array[@]}"; do
                pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
                if [[ "$item_lower" =~ $pattern_lower ]]; then
                    local current_confidence=1
                    
                    # Increase confidence for specific patterns
                    case "$pattern_lower" in
                        "update.app"|"*.ozip"|"*.kdz"|"ruu*.exe"|"*.ftf"|"*.nb0"|"*.pac")
                            current_confidence=3
                            ;;
                        "miui"|"samsung"|"huawei"|"oneplus"|"lg-"|"htc")
                            current_confidence=2
                            ;;
                    esac
                    
                    if [[ $current_confidence -gt $confidence ]]; then
                        detected_manufacturer="$manufacturer"
                        confidence=$current_confidence
                    fi
                    
                    detection_details+=("$manufacturer:$pattern:$item_name:$current_confidence")
                    break
                fi
            done
        done
    done < <(find "$firmware_path" -type f -print0)
    
    # Additional detection from build.prop or similar files
    detect_from_build_props "$firmware_path" detected_manufacturer confidence detection_details
    
    # Final manufacturer determination
    if [[ -n "$detected_manufacturer" && $confidence -gt 0 ]]; then
        msg_success "Manufacturer detected: ${detected_manufacturer^^} (confidence: $confidence)"
        
        # Show detection details in debug mode
        if [[ "${DEBUG:-0}" == "1" ]]; then
            msg_info "Detection details:"
            printf '%s\n' "${detection_details[@]}" | grep "^$detected_manufacturer:" | head -3
        fi
        
        echo "$detected_manufacturer"
        return 0
    else
        msg_warning "Could not reliably detect manufacturer"
        return 1
    fi
}

# Detect manufacturer from build.prop files
detect_from_build_props() {
    local firmware_path="$1"
    local -n manufacturer_ref=$2
    local -n confidence_ref=$3
    local -n details_ref=$4
    
    # Look for build.prop files
    while IFS= read -r -d '' prop_file; do
        # Extract manufacturer info from build.prop
        if [[ -f "$prop_file" ]]; then
            local brand
            local manufacturer
            local model
            
            brand=$(grep "ro.product.brand=" "$prop_file" 2>/dev/null | cut -d'=' -f2)
            manufacturer=$(grep "ro.product.manufacturer=" "$prop_file" 2>/dev/null | cut -d'=' -f2)
            model=$(grep "ro.product.model=" "$prop_file" 2>/dev/null | cut -d'=' -f2)
            
            # Map brand/manufacturer to our known manufacturers
            for known_manufacturer in "${!MANUFACTURER_PATTERNS[@]}"; do
                if [[ "${brand,,}" =~ $known_manufacturer ]] || [[ "${manufacturer,,}" =~ $known_manufacturer ]]; then
                    if [[ $confidence_ref -lt 3 ]]; then
                        manufacturer_ref="$known_manufacturer"
                        confidence_ref=3
                        details_ref+=("$known_manufacturer:build.prop:$brand/$manufacturer:3")
                    fi
                    break
                fi
            done
        fi
    done < <(find "$firmware_path" -name "build.prop" -o -name "default.prop" -print0)
}

# Get manufacturer-specific extraction methods
get_manufacturer_methods() {
    local manufacturer="$1"
    
    case "$manufacturer" in
        "samsung")
            echo "samsung_extract"
            ;;
        "xiaomi")
            echo "xiaomi_extract"
            ;;
        "huawei")
            echo "huawei_extract"
            ;;
        "oppo")
            echo "oppo_extract"
            ;;
        "lg")
            echo "lg_extract"
            ;;
        "htc")
            echo "htc_extract"
            ;;
        "sony")
            echo "sony_extract"
            ;;
        "motorola")
            echo "motorola_extract"
            ;;
        "nokia")
            echo "nokia_extract"
            ;;
        *)
            echo "generic_extract"
            ;;
    esac
}

# Samsung-specific extraction
samsung_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "Samsung firmware detected"
    
    # Handle Samsung .tar.md5 files
    while IFS= read -r -d '' tar_file; do
        msg_extract "Extracting Samsung TAR: $(basename "$tar_file")"
        tar -xf "$tar_file" -C "$output_dir" 2>/dev/null || {
            msg_warning "Failed to extract: $(basename "$tar_file")"
        }
    done < <(find "$firmware_path" -name "*.tar.md5" -o -name "*.tar" -print0)
    
    # Handle Samsung PIT files
    while IFS= read -r -d '' pit_file; do
        msg_info "Found Samsung PIT file: $(basename "$pit_file")"
        cp "$pit_file" "$output_dir/"
    done < <(find "$firmware_path" -name "*.pit" -print0)
}

# Xiaomi-specific extraction
xiaomi_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "Xiaomi firmware detected"
    
    # Handle MIUI firmware structure
    if [[ -d "$firmware_path/images" ]]; then
        msg_extract "Extracting Xiaomi fastboot images"
        cp -r "$firmware_path/images/"* "$output_dir/" 2>/dev/null
    fi
    
    # Handle TGZ files
    while IFS= read -r -d '' tgz_file; do
        msg_extract "Extracting Xiaomi TGZ: $(basename "$tgz_file")"
        tar -xzf "$tgz_file" -C "$output_dir" 2>/dev/null
    done < <(find "$firmware_path" -name "*.tgz" -print0)
}

# OPPO/OnePlus-specific extraction
oppo_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "OPPO/OnePlus firmware detected"
    
    # Handle OZIP files
    while IFS= read -r -d '' ozip_file; do
        msg_extract "Decrypting OZIP: $(basename "$ozip_file")"
        python3 "${OZIPDECRYPT}" "$ozip_file" "$output_dir" 2>/dev/null || {
            msg_warning "Failed to decrypt: $(basename "$ozip_file")"
        }
    done < <(find "$firmware_path" -name "*.ozip" -print0)
    
    # Handle OFP files
    while IFS= read -r -d '' ofp_file; do
        msg_extract "Extracting OFP: $(basename "$ofp_file")"
        python3 "${OFP_QC_DECRYPT}" "$ofp_file" "$output_dir" 2>/dev/null || {
            python3 "${OFP_MTK_DECRYPT}" "$ofp_file" "$output_dir" 2>/dev/null || {
                msg_warning "Failed to extract: $(basename "$ofp_file")"
            }
        }
    done < <(find "$firmware_path" -name "*.ofp" -print0)
    
    # Handle OPS files
    while IFS= read -r -d '' ops_file; do
        msg_extract "Decrypting OPS: $(basename "$ops_file")"
        python3 "${OPSDECRYPT}" "$ops_file" "$output_dir" 2>/dev/null || {
            msg_warning "Failed to decrypt: $(basename "$ops_file")"
        }
    done < <(find "$firmware_path" -name "*.ops" -print0)
}

# LG-specific extraction
lg_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "LG firmware detected"
    
    # Handle KDZ files
    while IFS= read -r -d '' kdz_file; do
        msg_extract "Extracting LG KDZ: $(basename "$kdz_file")"
        python3 "${UTILSDIR}/kdztools/unkdz.py" -f "$kdz_file" -x -o "$output_dir" 2>/dev/null || {
            msg_warning "Failed to extract: $(basename "$kdz_file")"
        }
    done < <(find "$firmware_path" -name "*.kdz" -print0)
}

# HTC-specific extraction
htc_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "HTC firmware detected"
    
    # Handle RUU files
    while IFS= read -r -d '' ruu_file; do
        msg_extract "Extracting HTC RUU: $(basename "$ruu_file")"
        "${RUUDECRYPT}" -s "$ruu_file" -o "$output_dir" 2>/dev/null || {
            msg_warning "Failed to extract: $(basename "$ruu_file")"
        }
    done < <(find "$firmware_path" -name "ruu*.exe" -print0)
}

# Generic extraction fallback
generic_extract() {
    local firmware_path="$1"
    local output_dir="$2"
    
    msg_device "Generic firmware extraction"
    
    # Copy all image files
    while IFS= read -r -d '' img_file; do
        msg_extract "Copying image: $(basename "$img_file")"
        cp "$img_file" "$output_dir/"
    done < <(find "$firmware_path" -name "*.img" -o -name "*.bin" -print0)
}

# Export functions
export -f detect_manufacturer detect_from_build_props get_manufacturer_methods
export -f samsung_extract xiaomi_extract oppo_extract lg_extract htc_extract generic_extract