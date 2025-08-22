#!/bin/bash
# DumprX Metadata Module - Extract firmware information from build properties
# Handles device information parsing and README generation

# Load required modules
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"

# Extract build property with fallback locations
get_build_prop() {
    local prop_name="$1"
    local locations=("${@:2}")
    local result
    
    # If no locations specified, use default locations
    if [[ ${#locations[@]} -eq 0 ]]; then
        locations=(
            "{system,system/system,vendor}/build*.prop"
            "vendor/build*.prop"
            "{system,system/system}/build*.prop"
            "product/build*.prop"
            "{oppo_product,my_product}/build*.prop"
            "vendor/euclid/*/build.prop"
            "vendor/euclid/product/build*.prop"
            "vendor/odm/etc/build*.prop"
        )
    fi
    
    # Try each location until we find a value
    for location in "${locations[@]}"; do
        result=$(grep -m1 -oP "(?<=^${prop_name}=).*" -hs ${location} 2>/dev/null | head -1)
        if [[ -n "${result}" ]]; then
            echo "${result}"
            return 0
        fi
    done
    
    return 1
}

# Extract device metadata
extract_device_metadata() {
    msg_process "Extracting device metadata from build properties"
    
    # Core build information
    local flavor platform manufacturer brand codename description incremental
    local fingerprint release id tags abilist locale density is_ab treble_support otaver
    local kernel_version
    
    # Extract flavor/version information
    flavor=$(get_build_prop "ro.build.flavor")
    [[ -z "${flavor}" ]] && flavor=$(get_build_prop "ro.vendor.build.flavor")
    [[ -z "${flavor}" ]] && flavor=$(get_build_prop "ro.system.build.flavor")
    
    # Extract tags
    tags=$(get_build_prop "ro.build.tags")
    [[ -z "${tags}" ]] && tags=$(get_build_prop "ro.vendor.build.tags")
    [[ -z "${tags}" ]] && tags=$(get_build_prop "ro.system.build.tags")
    
    # Extract platform
    platform=$(get_build_prop "ro.board.platform")
    [[ -z "${platform}" ]] && platform=$(get_build_prop "ro.vendor.board.platform")
    [[ -z "${platform}" ]] && platform=$(get_build_prop "ro.system.board.platform")
    
    # Extract manufacturer
    manufacturer=$(get_build_prop "ro.product.manufacturer")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.product.brand.sub" "system/system/euclid/my_product/build*.prop")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.vendor.product.manufacturer")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.product.vendor.manufacturer")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.system.product.manufacturer")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.product.system.manufacturer")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.product.odm.manufacturer" "vendor/odm/etc/build*.prop")
    [[ -z "${manufacturer}" ]] && manufacturer=$(get_build_prop "ro.product.product.manufacturer" "vendor/euclid/*/build.prop")
    
    # Extract fingerprint
    fingerprint=$(get_build_prop "ro.build.fingerprint" "{system,system/system}/build*.prop")
    [[ -z "${fingerprint}" ]] && fingerprint=$(get_build_prop "ro.vendor.build.fingerprint")
    [[ -z "${fingerprint}" ]] && fingerprint=$(get_build_prop "ro.system.build.fingerprint")
    [[ -z "${fingerprint}" ]] && fingerprint=$(get_build_prop "ro.product.build.fingerprint" "product/build*.prop")
    [[ -z "${fingerprint}" ]] && fingerprint=$(get_build_prop "ro.bootimage.build.fingerprint" "vendor/build.prop")
    
    # Extract brand
    brand=$(get_build_prop "ro.product.brand")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.product.brand.sub" "system/system/euclid/my_product/build*.prop")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.product.vendor.brand")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.vendor.product.brand")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.product.system.brand")
    [[ -z "${brand}" || "${brand}" == "OPPO" ]] && brand=$(get_build_prop "ro.product.system.brand" "vendor/euclid/*/build.prop")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.product.product.brand" "vendor/euclid/product/build*.prop")
    [[ -z "${brand}" ]] && brand=$(get_build_prop "ro.product.odm.brand" "vendor/odm/etc/build*.prop")
    [[ -z "${brand}" ]] && brand=$(echo "${fingerprint}" | cut -d'/' -f1)
    
    # Extract codename
    codename=$(get_build_prop "ro.product.device")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.vendor.product.device.oem" "vendor/euclid/odm/build.prop")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.product.vendor.device")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.vendor.product.device")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.product.system.device")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.product.product.device" "vendor/euclid/*/build.prop")
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.product.product.model" "vendor/euclid/*/build.prop")
    [[ -z "${codename}" ]] && codename=$(echo "${fingerprint}" | cut -d'/' -f3 | cut -d':' -f1)
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.build.fota.version" "{system,system/system}/build*.prop" | cut -d'-' -f1)
    [[ -z "${codename}" ]] && codename=$(get_build_prop "ro.build.product")
    
    # Extract release version
    release=$(get_build_prop "ro.build.version.release")
    [[ -z "${release}" ]] && release=$(get_build_prop "ro.vendor.build.version.release")
    [[ -z "${release}" ]] && release=$(get_build_prop "ro.system.build.version.release")
    
    # Extract build ID
    id=$(get_build_prop "ro.build.id")
    [[ -z "${id}" ]] && id=$(get_build_prop "ro.vendor.build.id")
    [[ -z "${id}" ]] && id=$(get_build_prop "ro.system.build.id")
    
    # Extract description
    description=$(get_build_prop "ro.build.description")
    [[ -z "${description}" ]] && description=$(get_build_prop "ro.vendor.build.description")
    [[ -z "${description}" ]] && description=$(get_build_prop "ro.system.build.description")
    [[ -z "${description}" ]] && description=$(get_build_prop "ro.product.build.description" "product/build*.prop")
    
    # Extract incremental
    incremental=$(get_build_prop "ro.build.version.incremental")
    [[ -z "${incremental}" ]] && incremental=$(get_build_prop "ro.vendor.build.version.incremental")
    [[ -z "${incremental}" ]] && incremental=$(get_build_prop "ro.system.build.version.incremental")
    
    # Special handling for Realme devices
    if [[ -z "${incremental}" && "${brand}" =~ "realme" ]]; then
        incremental=$(get_build_prop "ro.build.version.ota" "{vendor/euclid/product,oppo_product}/build.prop" | rev | cut -d'_' -f'1-2' | rev)
    fi
    
    # Fallback description and incremental
    [[ -z "${incremental}" && -n "${description}" ]] && incremental=$(echo "${description}" | cut -d' ' -f4)
    [[ -z "${description}" && -n "${incremental}" ]] && description="${flavor} ${release} ${id} ${incremental} ${tags}"
    [[ -z "${description}" && -z "${incremental}" ]] && description="${codename}"
    
    # Extract additional properties
    abilist=$(get_build_prop "ro.product.cpu.abilist" "{system,system/system}/build*.prop")
    [[ -z "${abilist}" ]] && abilist=$(get_build_prop "ro.vendor.product.cpu.abilist")
    
    locale=$(get_build_prop "ro.product.locale" "{system,system/system}/build*.prop")
    [[ -z "${locale}" ]] && locale="undefined"
    
    density=$(get_build_prop "ro.sf.lcd_density" "{system,system/system}/build*.prop")
    [[ -z "${density}" ]] && density="undefined"
    
    is_ab=$(get_build_prop "ro.build.ab_update")
    [[ -z "${is_ab}" ]] && is_ab="false"
    
    treble_support=$(get_build_prop "ro.treble.enabled" "{system,system/system}/build*.prop")
    [[ -z "${treble_support}" ]] && treble_support="false"
    
    otaver=$(get_build_prop "ro.build.version.ota" "{vendor/euclid/product,oppo_product,system,system/system}/build*.prop")
    [[ -z "${otaver}" ]] && otaver=$(get_build_prop "ro.build.fota.version" "{system,system/system}/build*.prop")
    
    # Extract kernel version if available
    if [[ -f "bootRE/ikconfig" ]]; then
        kernel_version=$(grep "Kernel Configuration" bootRE/ikconfig | head -1 | awk '{print $3}')
    fi
    
    # Clean and normalize values
    platform=$(echo "${platform}" | tr '[:upper:]' '[:lower:]' | tr -dc '[:print:]' | tr '_' '-' | cut -c 1-35)
    manufacturer=$(echo "${manufacturer}" | tr '[:upper:]' '[:lower:]' | tr -dc '[:print:]' | tr '_' '-' | cut -c 1-35)
    codename=$(echo "${codename}" | tr '[:upper:]' '[:lower:]' | tr -dc '[:print:]' | tr '_' '-' | cut -c 1-35)
    
    # Determine branch name
    local branch
    if [[ -n "${otaver}" && -z "${fingerprint}" ]]; then
        branch=$(echo "${otaver}" | tr ' ' '-')
    else
        branch=$(echo "${description}" | tr ' ' '-')
    fi
    
    # Set repository name based on target platform
    local repo
    if [[ "${PUSH_TO_GITLAB}" == "true" ]]; then
        repo=$(printf "%s" "${brand}" | tr '[:upper:]' '[:lower:]')/${codename}
    else
        repo=$(echo "${brand}_${codename}_dump" | tr '[:upper:]' '[:lower:]')
    fi
    
    # Export all variables for use by other functions
    export DEVICE_MANUFACTURER="${manufacturer}"
    export DEVICE_BRAND="${brand}"
    export DEVICE_CODENAME="${codename}"
    export DEVICE_PLATFORM="${platform}"
    export DEVICE_FLAVOR="${flavor}"
    export DEVICE_RELEASE="${release}"
    export DEVICE_ID="${id}"
    export DEVICE_INCREMENTAL="${incremental}"
    export DEVICE_TAGS="${tags}"
    export DEVICE_DESCRIPTION="${description}"
    export DEVICE_FINGERPRINT="${fingerprint}"
    export DEVICE_ABILIST="${abilist}"
    export DEVICE_LOCALE="${locale}"
    export DEVICE_DENSITY="${density}"
    export DEVICE_IS_AB="${is_ab}"
    export DEVICE_TREBLE="${treble_support}"
    export DEVICE_OTAVER="${otaver}"
    export DEVICE_KERNEL="${kernel_version}"
    export DEVICE_BRANCH="${branch}"
    export DEVICE_REPO="${repo}"
    
    msg_success "Device metadata extracted successfully"
    msg_info "Device: ${brand} ${codename} (${description})"
}

# Generate README file
generate_readme() {
    local output_dir="${1:-${OUTDIR}}"
    
    msg_process "Generating README file"
    
    if [[ -z "${DEVICE_DESCRIPTION}" ]]; then
        msg_warning "Device metadata not extracted, extracting now"
        extract_device_metadata
    fi
    
    cat > "${output_dir}/README.md" << EOF
## ${DEVICE_DESCRIPTION}

### Device Information
- **Manufacturer**: ${DEVICE_MANUFACTURER}
- **Brand**: ${DEVICE_BRAND}
- **Codename**: ${DEVICE_CODENAME}
- **Platform**: ${DEVICE_PLATFORM}

### Build Information
- **Flavor**: ${DEVICE_FLAVOR}
- **Release Version**: ${DEVICE_RELEASE}
- **Build ID**: ${DEVICE_ID}
- **Incremental**: ${DEVICE_INCREMENTAL}
- **Tags**: ${DEVICE_TAGS}
- **OTA Version**: ${DEVICE_OTAVER}

### System Information
- **Kernel Version**: ${DEVICE_KERNEL}
- **CPU Abilist**: ${DEVICE_ABILIST}
- **A/B Device**: ${DEVICE_IS_AB}
- **Treble Support**: ${DEVICE_TREBLE}
- **Locale**: ${DEVICE_LOCALE}
- **Screen Density**: ${DEVICE_DENSITY}

### Technical Details
- **Fingerprint**: ${DEVICE_FINGERPRINT}
- **Branch**: ${DEVICE_BRANCH}
- **Repository**: ${DEVICE_REPO}

---
*Generated by DumprX - Firmware extraction and analysis toolkit*
EOF
    
    msg_success "README generated at ${output_dir}/README.md"
    
    # Display the README content
    show_title "Device Information Summary"
    cat "${output_dir}/README.md"
}

# Get a specific device property
get_device_property() {
    local property="$1"
    
    case "${property}" in
        manufacturer) echo "${DEVICE_MANUFACTURER}" ;;
        brand) echo "${DEVICE_BRAND}" ;;
        codename) echo "${DEVICE_CODENAME}" ;;
        platform) echo "${DEVICE_PLATFORM}" ;;
        description) echo "${DEVICE_DESCRIPTION}" ;;
        fingerprint) echo "${DEVICE_FINGERPRINT}" ;;
        release) echo "${DEVICE_RELEASE}" ;;
        incremental) echo "${DEVICE_INCREMENTAL}" ;;
        branch) echo "${DEVICE_BRANCH}" ;;
        repo) echo "${DEVICE_REPO}" ;;
        is_ab) echo "${DEVICE_IS_AB}" ;;
        treble) echo "${DEVICE_TREBLE}" ;;
        *) 
            msg_error "Unknown property: ${property}"
            return 1
            ;;
    esac
}