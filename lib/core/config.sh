#!/bin/bash
# DumprX Core Configuration Module
# Centralized configuration management

# Set strict error handling
set -euo pipefail

# Global configuration variables
declare -g PROJECT_DIR
declare -g INPUTDIR
declare -g UTILSDIR
declare -g OUTDIR
declare -g TMPDIR

# Initialize project directories
init_directories() {
    PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && cd ../.. && pwd )"
    
    # Validate project directory path
    if [[ "$PROJECT_DIR" =~ [[:space:]] ]]; then
        echo "ERROR: Project directory path contains spaces. Please move to a proper UNIX-formatted folder."
        exit 1
    fi
    
    # Set directory paths
    INPUTDIR="${PROJECT_DIR}/input"
    UTILSDIR="${PROJECT_DIR}/utils"
    OUTDIR="${PROJECT_DIR}/out"
    TMPDIR="${OUTDIR}/tmp"
    
    # Create directories
    rm -rf "${TMPDIR}" 2>/dev/null || true
    mkdir -p "${OUTDIR}" "${TMPDIR}" "${INPUTDIR}" 2>/dev/null
}

# Partition definitions
declare -g PARTITIONS="system system_ext system_other systemex vendor cust odm oem factory product xrom modem dtbo dtb boot vendor_boot recovery tz oppo_product preload_common opproduct reserve india my_preload my_odm my_stock my_operator my_country my_product my_company my_engineering my_heytap my_custom my_manifest my_carrier my_region my_bigball my_version special_preload system_dlkm vendor_dlkm odm_dlkm init_boot vendor_kernel_boot odmko socko nt_log mi_ext hw_product product_h preas preavs"

declare -g EXT4PARTITIONS="system vendor cust odm oem factory product xrom systemex oppo_product preload_common hw_product product_h preas preavs"

declare -g OTHERPARTITIONS="tz.mbn:tz tz.img:tz modem.img:modem NON-HLOS:modem boot-verified.img:boot recovery-verified.img:recovery dtbo-verified.img:dtbo"

# External tools configuration
declare -g EXTERNAL_TOOLS=(
    "bkerler/oppo_ozip_decrypt"
    "bkerler/oppo_decrypt"
    "marin-m/vmlinux-to-elf"
    "ShivamKumarJha/android_tools"
    "HemanthJabalpuri/pacextractor"
)

# Tool path aliases
declare -g SDAT2IMG
declare -g SIMG2IMG
declare -g PACKSPARSEIMG
declare -g UNSIN
declare -g PAYLOAD_EXTRACTOR
declare -g DTC
declare -g VMLINUX2ELF
declare -g KALLSYMS_FINDER
declare -g OZIPDECRYPT
declare -g OFP_QC_DECRYPT
declare -g OFP_MTK_DECRYPT
declare -g OPSDECRYPT
declare -g LPUNPACK
declare -g UNPACKBOOT
declare -g EXTRACT_IKCONFIG
declare -g RUUDECRYPT
declare -g AML_EXTRACT
declare -g BIN_7ZZ

# Initialize tool paths
init_tool_paths() {
    SDAT2IMG="${UTILSDIR}/sdat2img.py"
    SIMG2IMG="${UTILSDIR}/bin/simg2img"
    PACKSPARSEIMG="${UTILSDIR}/bin/packsparseimg"
    UNSIN="${UTILSDIR}/unsin"
    PAYLOAD_EXTRACTOR="${UTILSDIR}/bin/payload-dumper-go"
    DTC="${UTILSDIR}/dtc"
    VMLINUX2ELF="${UTILSDIR}/vmlinux-to-elf/vmlinux-to-elf"
    KALLSYMS_FINDER="${UTILSDIR}/vmlinux-to-elf/kallsyms-finder"
    OZIPDECRYPT="${UTILSDIR}/oppo_ozip_decrypt/ozipdecrypt.py"
    OFP_QC_DECRYPT="${UTILSDIR}/oppo_decrypt/ofp_qc_decrypt.py"
    OFP_MTK_DECRYPT="${UTILSDIR}/oppo_decrypt/ofp_mtk_decrypt.py"
    OPSDECRYPT="${UTILSDIR}/oppo_decrypt/opscrypto.py"
    LPUNPACK="${UTILSDIR}/lpunpack"
    UNPACKBOOT="${UTILSDIR}/unpackboot.sh"
    EXTRACT_IKCONFIG="${UTILSDIR}/extract-ikconfig"
    RUUDECRYPT="${UTILSDIR}/RUU_Decrypt_Tool"
    AML_EXTRACT="${UTILSDIR}/aml-upgrade-package-extract"
    BIN_7ZZ="7zz"
}

# Initialize configuration
init_config() {
    init_directories
    init_tool_paths
}

# Export functions for use in other modules
export -f init_directories init_tool_paths init_config