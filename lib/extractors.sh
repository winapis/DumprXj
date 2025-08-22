#!/bin/bash
# DumprX Firmware Extraction Module - Handle various firmware formats
# Provides extraction functions for different firmware types

# Load required modules
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"
source "$(dirname "${BASH_SOURCE[0]}")/utils.sh"

# Tool paths (will be initialized by init_extractors)
declare -g SDAT2IMG SIMG2IMG PACKSPARSEIMG UNSIN PAYLOAD_EXTRACTOR DTC
declare -g VMLINUX2ELF KALLSYMS_FINDER OZIPDECRYPT OFP_QC_DECRYPT OFP_MTK_DECRYPT
declare -g OPSDECRYPT LPUNPACK SPLITUAPP PACEXTRACTOR NB0_EXTRACT KDZ_EXTRACT
declare -g DZ_EXTRACT RUUDECRYPT EXTRACT_IKCONFIG UNPACKBOOT AML_EXTRACT
declare -g AFPTOOL_EXTRACT RK_EXTRACT BIN_7ZZ FSCK_EROFS

# Partition definitions
declare -r PARTITIONS="system system_ext system_other systemex vendor cust odm oem factory product xrom modem dtbo dtb boot vendor_boot recovery tz oppo_product preload_common opproduct reserve india my_preload my_odm my_stock my_operator my_country my_product my_company my_engineering my_heytap my_custom my_manifest my_carrier my_region my_bigball my_version special_preload system_dlkm vendor_dlkm odm_dlkm init_boot vendor_kernel_boot odmko socko nt_log mi_ext hw_product product_h preas preavs"

declare -r EXT4PARTITIONS="system vendor cust odm oem factory product xrom systemex oppo_product preload_common hw_product product_h preas preavs"

declare -r OTHERPARTITIONS="tz.mbn:tz tz.img:tz modem.img:modem NON-HLOS:modem boot-verified.img:boot recovery-verified.img:recovery dtbo-verified.img:dtbo"

# Initialize extractor tool paths
init_extractors() {
    # Core tools
    SDAT2IMG="${UTILSDIR}/sdat2img.py"
    SIMG2IMG="${UTILSDIR}/bin/simg2img"
    PACKSPARSEIMG="${UTILSDIR}/bin/packsparseimg"
    UNSIN="${UTILSDIR}/unsin"
    PAYLOAD_EXTRACTOR="${UTILSDIR}/bin/payload-dumper-go"
    DTC="${UTILSDIR}/dtc"
    
    # Advanced tools
    VMLINUX2ELF="${UTILSDIR}/vmlinux-to-elf/vmlinux-to-elf"
    KALLSYMS_FINDER="${UTILSDIR}/vmlinux-to-elf/kallsyms-finder"
    
    # Brand-specific tools
    OZIPDECRYPT="${UTILSDIR}/oppo_ozip_decrypt/ozipdecrypt.py"
    OFP_QC_DECRYPT="${UTILSDIR}/oppo_decrypt/ofp_qc_decrypt.py"
    OFP_MTK_DECRYPT="${UTILSDIR}/oppo_decrypt/ofp_mtk_decrypt.py"
    OPSDECRYPT="${UTILSDIR}/oppo_decrypt/opscrypto.py"
    
    # Archive and image tools
    LPUNPACK="${UTILSDIR}/lpunpack"
    SPLITUAPP="${UTILSDIR}/splituapp.py"
    PACEXTRACTOR="${UTILSDIR}/pacextractor/python/pacExtractor.py"
    NB0_EXTRACT="${UTILSDIR}/nb0-extract"
    KDZ_EXTRACT="${UTILSDIR}/kdztools/unkdz.py"
    DZ_EXTRACT="${UTILSDIR}/kdztools/undz.py"
    RUUDECRYPT="${UTILSDIR}/RUU_Decrypt_Tool"
    EXTRACT_IKCONFIG="${UTILSDIR}/extract-ikconfig"
    UNPACKBOOT="${UTILSDIR}/unpackboot.sh"
    AML_EXTRACT="${UTILSDIR}/aml-upgrade-package-extract"
    AFPTOOL_EXTRACT="${UTILSDIR}/bin/afptool"
    RK_EXTRACT="${UTILSDIR}/bin/rkImageMaker"
    
    # File system tools
    FSCK_EROFS="${UTILSDIR}/bin/fsck.erofs"
    
    # 7zip (check if system version exists)
    if ! command_exists 7zz; then
        BIN_7ZZ="${UTILSDIR}/bin/7zz"
    else
        BIN_7ZZ="7zz"
    fi
}

# Extract super image partitions
extract_super_image() {
    local super_file="${1:-super.img}"
    
    if [[ ! -f "${super_file}" ]]; then
        msg_warning "Super image not found: ${super_file}"
        return 1
    fi
    
    msg_process "Extracting partitions from super image"
    
    # Convert sparse to raw if needed
    if file "${super_file}" | grep -q "Android sparse"; then
        msg_info "Converting sparse super image to raw"
        "${SIMG2IMG}" "${super_file}" "${super_file}.raw" 2>/dev/null
        if [[ -s "${super_file}.raw" ]]; then
            mv "${super_file}.raw" "${super_file}"
        fi
    fi
    
    local extracted_count=0
    
    # Extract each partition
    for partition in ${PARTITIONS}; do
        msg_info "Extracting partition: ${partition}"
        
        # Try _a suffix first (A/B partitions)
        if "${LPUNPACK}" --partition="${partition}_a" "${super_file}" 2>/dev/null; then
            if [[ -f "${partition}_a.img" ]]; then
                mv "${partition}_a.img" "${partition}.img"
                ((extracted_count++))
                msg_success "Extracted ${partition} (A/B slot)"
            fi
        # Try without suffix
        elif "${LPUNPACK}" --partition="${partition}" "${super_file}" 2>/dev/null; then
            if [[ -f "${partition}.img" ]]; then
                ((extracted_count++))
                msg_success "Extracted ${partition}"
            fi
        fi
    done
    
    # Clean up temporary files
    rm -f "${super_file}.raw" 2>/dev/null
    
    msg_success "Extracted ${extracted_count} partitions from super image"
    return 0
}

# Detect and extract OZIP files
extract_ozip() {
    local filepath="$1"
    local filename="$2"
    
    # Check OZIP magic bytes
    if [[ $(head -c12 "${filepath}" 2>/dev/null | tr -d '\0') == "OPPOENCRYPT!" ]] || [[ "${filepath##*.}" == "ozip" ]]; then
        msg_process "Oppo/Realme OZIP detected"
        
        # Copy file to temp directory
        copy_with_progress "${filepath}" "${TMPDIR}/${filename}" "Copying OZIP file"
        
        msg_process "Decrypting OZIP and creating ZIP"
        uv run --with-requirements "${UTILSDIR}/oppo_decrypt/requirements.txt" "${OZIPDECRYPT}" "${TMPDIR}/${filename}"
        
        # Move decrypted content
        mkdir -p "${INPUTDIR}" 2>/dev/null
        rm -rf "${INPUTDIR:?}"/* 2>/dev/null
        
        if [[ -f "${filename%.*}.zip" ]]; then
            mv "${filename%.*}.zip" "${INPUTDIR}"/
            msg_success "OZIP decrypted to ZIP"
        elif [[ -d "${TMPDIR}/out" ]]; then
            mv "${TMPDIR}"/out/* "${INPUTDIR}"/
            msg_success "OZIP extracted directly"
        else
            msg_error "OZIP decryption failed"
            return 1
        fi
        
        cleanup_temp "${TMPDIR}"
        return 0
    fi
    
    return 1
}

# Extract OPS files
extract_ops() {
    local filepath="$1"
    local filename="$2"
    
    if [[ "${filepath##*.}" == "ops" ]]; then
        msg_process "Oppo/OnePlus OPS detected"
        
        # Copy file to temp directory
        copy_with_progress "${filepath}" "${TMPDIR}/${filename}" "Copying OPS file"
        
        msg_process "Decrypting and extracting OPS"
        uv run --with-requirements "${UTILSDIR}/oppo_decrypt/requirements.txt" "${OPSDECRYPT}" decrypt "${TMPDIR}/${filename}"
        
        # Move extracted content
        mkdir -p "${INPUTDIR}" 2>/dev/null
        rm -rf "${INPUTDIR:?}"/* 2>/dev/null
        
        if [[ -d "${TMPDIR}/extract" ]]; then
            mv "${TMPDIR}"/extract/* "${INPUTDIR}"/
            msg_success "OPS file extracted"
        else
            msg_error "OPS extraction failed"
            return 1
        fi
        
        cleanup_temp "${TMPDIR}"
        return 0
    fi
    
    return 1
}

# Extract OFP files
extract_ofp() {
    local filepath="$1"
    local filename="$2"
    
    if [[ "${filepath##*.}" == "ofp" ]]; then
        msg_process "Oppo OFP detected"
        
        # Copy file to temp directory
        copy_with_progress "${filepath}" "${TMPDIR}/${filename}" "Copying OFP file"
        
        # Detect OFP type and extract accordingly
        msg_process "Analyzing OFP file type"
        
        # Try Qualcomm OFP first
        if uv run --with-requirements "${UTILSDIR}/oppo_decrypt/requirements.txt" "${OFP_QC_DECRYPT}" "${TMPDIR}/${filename}" 2>/dev/null; then
            msg_success "Qualcomm OFP extracted"
        # Try MediaTek OFP
        elif uv run --with-requirements "${UTILSDIR}/oppo_decrypt/requirements.txt" "${OFP_MTK_DECRYPT}" "${TMPDIR}/${filename}" 2>/dev/null; then
            msg_success "MediaTek OFP extracted"
        else
            msg_error "OFP extraction failed"
            return 1
        fi
        
        # Move extracted content
        mkdir -p "${INPUTDIR}" 2>/dev/null
        rm -rf "${INPUTDIR:?}"/* 2>/dev/null
        
        if [[ -d "${TMPDIR}/out" ]]; then
            mv "${TMPDIR}"/out/* "${INPUTDIR}"/
        fi
        
        cleanup_temp "${TMPDIR}"
        return 0
    fi
    
    return 1
}

# Extract KDZ files (LG)
extract_kdz() {
    local filepath="$1"
    local filename="$2"
    
    if echo "${filepath}" | grep -q ".*.kdz" || [[ "${filepath##*.}" == "kdz" ]]; then
        msg_process "LG KDZ detected"
        
        # Copy file to temp directory
        copy_with_progress "${filepath}" "${TMPDIR}/${filename}" "Copying KDZ file"
        
        msg_process "Extracting KDZ file"
        python3 "${KDZ_EXTRACT}" -f "${filename}" -x -o "./" 2>/dev/null
        
        # Find and extract DZ file
        local dzfile
        dzfile=$(ls -- *.dz 2>/dev/null | head -1)
        
        if [[ -n "${dzfile}" ]]; then
            msg_process "Extracting DZ partitions from ${dzfile}"
            python3 "${DZ_EXTRACT}" -f "${dzfile}" -s -o "./" 2>/dev/null
            msg_success "KDZ extraction completed"
        else
            msg_error "No DZ file found in KDZ"
            return 1
        fi
        
        return 0
    fi
    
    return 1
}

# Extract payload.bin files
extract_payload() {
    local payload_file="${1:-payload.bin}"
    
    if [[ -f "${payload_file}" ]]; then
        msg_process "Extracting payload.bin"
        
        if [[ -x "${PAYLOAD_EXTRACTOR}" ]]; then
            "${PAYLOAD_EXTRACTOR}" -o ./ "${payload_file}"
            msg_success "Payload extraction completed"
        else
            msg_error "Payload extractor not found"
            return 1
        fi
        
        return 0
    fi
    
    return 1
}

# Extract UPDATE.APP files (Huawei)
extract_update_app() {
    local update_file="${1:-UPDATE.APP}"
    
    if [[ -f "${update_file}" ]]; then
        msg_process "Extracting UPDATE.APP"
        
        if python3 "${SPLITUAPP}" "${update_file}"; then
            msg_success "UPDATE.APP extraction completed"
        else
            msg_error "UPDATE.APP extraction failed"
            return 1
        fi
        
        return 0
    fi
    
    return 1
}

# Extract system.new.dat files
extract_system_dat() {
    local dat_file="${1:-system.new.dat}"
    local transfer_list="${2:-system.transfer.list}"
    local output_file="${3:-system.img}"
    
    if [[ -f "${dat_file}" && -f "${transfer_list}" ]]; then
        msg_process "Converting system.new.dat to system.img"
        
        # Handle compressed dat files
        local working_dat="${dat_file}"
        
        if [[ "${dat_file}" == *.br ]]; then
            msg_info "Decompressing brotli-compressed dat file"
            brotli -d "${dat_file}" -o "${dat_file%.br}"
            working_dat="${dat_file%.br}"
        elif [[ "${dat_file}" == *.xz ]]; then
            msg_info "Decompressing xz-compressed dat file"
            xz -d "${dat_file}"
            working_dat="${dat_file%.xz}"
        fi
        
        if python3 "${SDAT2IMG}" "${transfer_list}" "${working_dat}" "${output_file}"; then
            msg_success "system.new.dat converted to ${output_file}"
            
            # Clean up intermediate files
            [[ "${working_dat}" != "${dat_file}" ]] && rm -f "${working_dat}"
        else
            msg_error "system.new.dat conversion failed"
            return 1
        fi
        
        return 0
    fi
    
    return 1
}

# Main extraction dispatcher
extract_firmware() {
    local filepath="$1"
    local filename="${2:-$(basename "${filepath}")}"
    
    msg_process "Starting firmware extraction"
    msg_info "File: ${filename}"
    msg_info "Format: $(detect_format "${filepath}")"
    
    # Try format-specific extractors
    if extract_ozip "${filepath}" "${filename}"; then
        return 0
    elif extract_ops "${filepath}" "${filename}"; then
        return 0
    elif extract_ofp "${filepath}" "${filename}"; then
        return 0
    elif extract_kdz "${filepath}" "${filename}"; then
        return 0
    fi
    
    # Try common files in current directory
    extract_payload "payload.bin"
    extract_update_app "UPDATE.APP"
    extract_system_dat "system.new.dat" "system.transfer.list" "system.img"
    extract_super_image "super.img"
    
    msg_success "Firmware extraction process completed"
    return 0
}