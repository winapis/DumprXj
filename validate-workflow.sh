#!/bin/bash
# DumprX Workflow Validation Script - Refactored
# Validates that all components needed for the GitHub Actions workflow are working

# Get script directory for module loading
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

# Load modules
source "${SCRIPT_DIR}/lib/ui.sh"
source "${SCRIPT_DIR}/lib/utils.sh"

# Validation functions
validate_workflow_file() {
    show_section "Workflow File Validation"
    
    local workflow_file=".github/workflows/firmware-dump.yml"
    
    if [[ -f "${workflow_file}" ]]; then
        msg_success "Workflow file exists"
        
        if python3 -c "import yaml; yaml.safe_load(open('${workflow_file}'))" 2>/dev/null; then
            msg_success "Workflow YAML syntax is valid"
            return 0
        else
            msg_error "Workflow YAML syntax is invalid"
            return 1
        fi
    else
        msg_error "Workflow file not found: ${workflow_file}"
        return 1
    fi
}

validate_setup_script() {
    show_section "Setup Script Validation"
    
    if [[ -f "setup.sh" && -x "setup.sh" ]]; then
        msg_success "Setup script exists and is executable"
        return 0
    else
        msg_error "Setup script not found or not executable"
        return 1
    fi
}

validate_dumper_script() {
    show_section "Dumper Script Validation"
    
    if [[ -f "dumper.sh" && -x "dumper.sh" ]]; then
        msg_success "Dumper script exists and is executable"
        return 0
    else
        msg_error "Dumper script not found or not executable"
        return 1
    fi
}

validate_git_lfs() {
    show_section "Git LFS Validation"
    
    if command_exists git-lfs; then
        msg_success "Git LFS is available"
        return 0
    else
        msg_error "Git LFS not found"
        return 1
    fi
}

validate_token_logic() {
    show_section "Token File Logic Validation"
    
    local test_token_file=".test_token"
    echo "test_token" > "${test_token_file}"
    
    if [[ -s "${test_token_file}" ]]; then
        msg_success "Token file creation and reading works"
        rm -f "${test_token_file}"
        return 0
    else
        msg_error "Token file logic failed"
        rm -f "${test_token_file}"
        return 1
    fi
}

validate_gitignore() {
    show_section "Gitignore Validation"
    
    if grep -q "github_token\|gitlab_token" .gitignore 2>/dev/null; then
        msg_success "Sensitive files are in .gitignore"
        return 0
    else
        msg_error "Token files not properly ignored"
        return 1
    fi
}

validate_documentation() {
    show_section "Documentation Validation"
    
    local errors=0
    
    if grep -q "GitHub Actions Workflow Usage" README.md 2>/dev/null; then
        msg_success "Workflow documentation exists in README"
    else
        msg_error "Workflow documentation missing from README"
        ((errors++))
    fi
    
    if [[ -f "WORKFLOW_EXAMPLES.md" ]]; then
        msg_success "Workflow examples file exists"
    else
        msg_error "Workflow examples file missing"
        ((errors++))
    fi
    
    return ${errors}
}

validate_modules() {
    show_section "Module System Validation"
    
    local lib_dir="lib"
    local required_modules=(
        "ui.sh"
        "utils.sh"
        "git.sh"
        "downloader.sh"
        "extractors.sh"
        "metadata.sh"
        "setup.sh"
        "loader.sh"
    )
    
    local missing_modules=()
    
    for module in "${required_modules[@]}"; do
        if [[ ! -f "${lib_dir}/${module}" ]]; then
            missing_modules+=("${module}")
        fi
    done
    
    if [[ ${#missing_modules[@]} -eq 0 ]]; then
        msg_success "All required modules are present"
        return 0
    else
        msg_error "Missing modules: ${missing_modules[*]}"
        return 1
    fi
}

validate_dependencies() {
    show_section "Dependency Validation"
    
    local required_commands=("python3" "git" "curl" "wget")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "${cmd}"; then
            missing_commands+=("${cmd}")
        fi
    done
    
    if [[ ${#missing_commands[@]} -eq 0 ]]; then
        msg_success "All required dependencies are available"
        return 0
    else
        msg_warning "Missing dependencies: ${missing_commands[*]}"
        return 1
    fi
}

# Main validation function
run_validation() {
    local total_tests=0
    local passed_tests=0
    
    # Run all validation tests
    local validation_tests=(
        "validate_workflow_file"
        "validate_setup_script"
        "validate_dumper_script"
        "validate_git_lfs"
        "validate_token_logic"
        "validate_gitignore"
        "validate_documentation"
        "validate_modules"
        "validate_dependencies"
    )
    
    for test in "${validation_tests[@]}"; do
        ((total_tests++))
        if "${test}"; then
            ((passed_tests++))
        fi
        echo
    done
    
    # Display results
    show_title "Validation Results"
    echo
    msg_info "Tests passed: ${passed_tests}/${total_tests}"
    echo
    
    if [[ ${passed_tests} -eq ${total_tests} ]]; then
        msg_success "🎉 All validation checks passed!"
        echo
        msg_info "Your DumprX repository is ready for the GitHub Actions workflow!"
        echo
        show_section "Usage Instructions"
        echo "To use the workflow:"
        echo "1. Go to the Actions tab in your GitHub repository"
        echo "2. Select 'Firmware Dump Workflow'"
        echo "3. Click 'Run workflow'"
        echo "4. Fill in the required parameters and run"
        echo
        return 0
    else
        msg_error "Some validation checks failed"
        echo
        msg_info "Please fix the issues above before using the workflow"
        echo
        return 1
    fi
}

# Main execution
main() {
    # Initialize UI
    init_ui
    
    show_title "DumprX Workflow Validation"
    msg_info "Validating all components needed for GitHub Actions workflow"
    echo
    
    # Run validation
    run_validation
}

# Execute main function
main "$@"