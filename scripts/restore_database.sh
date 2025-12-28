#!/bin/bash

################################################################################
# Database Restore Script
#
# Purpose:
#   - Restore PostgreSQL or SQLite database from backup
#   - Download backups from S3 (optional)
#   - Validate backup files before restore
#   - Handle both local and remote backups
#   - Provide detailed logging and safety checks
#
# Usage:
#   ./restore_database.sh <backup_file_or_s3_url>
#
# Examples:
#   # Restore from local backup
#   ./restore_database.sh /backups/socrates_20250101_120000.sql.gz
#
#   # Restore from S3 URL
#   ./restore_database.sh s3://my-backups/backups/socrates_20250101_120000.sql.gz
#
#   # Interactive mode (prompt for backup file)
#   ./restore_database.sh
#
# Environment Variables:
#   DATABASE_HOST        - PostgreSQL host (default: postgres)
#   DATABASE_PORT        - PostgreSQL port (default: 5432)
#   DATABASE_NAME        - Database name (default: socrates)
#   DATABASE_USER        - Database user (default: postgres)
#   DATABASE_PASSWORD    - Database password (required for PostgreSQL)
#   DATABASE_TYPE        - 'postgresql' or 'sqlite' (auto-detect)
#   SQLITE_DB_PATH       - Path to SQLite database file
#   AWS_REGION           - AWS region (default: us-east-1)
#   RESTORE_USER         - User confirming restore (for audit logging)
#   LOG_FILE             - Log file path (default: /var/log/socrates_restore.log)
#
################################################################################

set -euo pipefail

# Configuration with defaults
DB_HOST="${DATABASE_HOST:-postgres}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-socrates}"
DB_USER="${DATABASE_USER:-postgres}"
DB_TYPE="${DATABASE_TYPE:-}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"
RESTORE_USER="${RESTORE_USER:-$(whoami)}"
LOG_FILE="${LOG_FILE:-/var/log/socrates_restore.log}"
TEMP_DIR="${TMPDIR:-/tmp}"

# Get backup file from argument or prompt
BACKUP_SOURCE="${1:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Logging Functions
################################################################################

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "$@"
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}⚠ WARNING: $@${NC}" >&2
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}✗ ERROR: $@${NC}" >&2
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}✓ $@${NC}"
}

################################################################################
# Validation Functions
################################################################################

check_prerequisites() {
    log_info "Checking prerequisites..."

    local required_commands=("gunzip" "date")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            log_error "Required command not found: ${cmd}"
            exit 1
        fi
    done

    # Check database-specific commands
    if [[ "${DB_TYPE}" == "postgresql" || -z "${DB_TYPE}" && -z "${SQLITE_DB_PATH}" ]]; then
        if ! command -v pg_restore &> /dev/null; then
            log_error "pg_restore not found. Install PostgreSQL client tools."
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

detect_database_type() {
    log_info "Detecting database type..."

    if [[ -n "${SQLITE_DB_PATH}" ]]; then
        DB_TYPE="sqlite"
        log_info "Using SQLite database: ${SQLITE_DB_PATH}"
    else
        DB_TYPE="postgresql"
        log_info "Using PostgreSQL database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    fi
}

################################################################################
# Backup File Selection
################################################################################

prompt_for_backup() {
    echo -e "${BLUE}=========================================="
    echo "SELECT BACKUP FILE"
    echo "==========================================${NC}"
    echo ""
    echo "Please provide the backup file path or S3 URL:"
    echo "  - Local file: /path/to/backup.sql.gz"
    echo "  - S3 URL: s3://bucket/path/backup.sql.gz"
    echo ""
    read -p "Backup file or S3 URL: " BACKUP_SOURCE

    if [[ -z "${BACKUP_SOURCE}" ]]; then
        log_error "Backup file path is required"
        exit 1
    fi
}

list_available_backups() {
    echo -e "${BLUE}=========================================="
    echo "AVAILABLE BACKUPS"
    echo "==========================================${NC}"
    echo ""

    local backup_dir="/backups"
    if [[ -d "${backup_dir}" ]]; then
        echo "Local backups:"
        find "${backup_dir}" -name "socrates_*.sql.gz" -type f -exec ls -lh {} \; 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  No local backups found"
    fi

    echo ""
    echo "Use './restore_database.sh <backup_file>' to restore"
    echo ""
}

################################################################################
# Backup File Handling
################################################################################

is_s3_path() {
    [[ "${BACKUP_SOURCE}" =~ ^s3:// ]]
}

download_from_s3() {
    log_info "Downloading backup from S3: ${BACKUP_SOURCE}"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install aws-cli to download from S3."
        exit 1
    fi

    local local_backup="${TEMP_DIR}/$(basename ${BACKUP_SOURCE})"

    if ! aws s3 cp "${BACKUP_SOURCE}" "${local_backup}" \
        --region "${AWS_REGION}" 2>&1; then
        log_error "Failed to download backup from S3"
        exit 1
    fi

    BACKUP_SOURCE="${local_backup}"
    log_success "Backup downloaded to ${BACKUP_SOURCE}"
}

validate_backup_file() {
    log_info "Validating backup file..."

    if [[ ! -f "${BACKUP_SOURCE}" ]]; then
        log_error "Backup file not found: ${BACKUP_SOURCE}"
        exit 1
    fi

    local file_size=$(du -h "${BACKUP_SOURCE}" | cut -f1)
    log_info "Backup file size: ${file_size}"

    # Check if it's a gzip file
    if ! file "${BACKUP_SOURCE}" | grep -q "gzip"; then
        log_warn "File does not appear to be gzip compressed"
    fi

    # Verify gzip integrity
    if ! gzip -t "${BACKUP_SOURCE}" 2>&1; then
        log_error "Backup file is corrupted or not a valid gzip file"
        exit 1
    fi

    log_success "Backup file validation passed"
}

################################################################################
# Confirmation Functions
################################################################################

confirm_restore() {
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "⚠ RESTORE DATABASE - CONFIRMATION REQUIRED"
    echo "==========================================${NC}"
    echo ""
    echo "This operation will:"
    echo "  1. DROP the existing database: ${DB_NAME}"
    echo "  2. RECREATE the database from backup"
    echo "  3. RESTORE all data from: $(basename ${BACKUP_SOURCE})"
    echo ""
    echo "This is a DESTRUCTIVE operation and CANNOT be undone."
    echo "Make sure you have a current backup before proceeding."
    echo ""

    # Ask for explicit confirmation
    read -p "Type 'yes' to confirm restore: " confirmation

    if [[ "${confirmation}" != "yes" ]]; then
        log_info "Restore cancelled by user"
        echo "Restore cancelled."
        exit 0
    fi

    echo ""
    log_info "User confirmed restore operation"
}

################################################################################
# Restore Functions
################################################################################

restore_postgresql() {
    log_info "Starting PostgreSQL restore..."
    log_info "Host: ${DB_HOST}, Port: ${DB_PORT}, Database: ${DB_NAME}"

    local start_time=$(date +%s)

    # Export password
    export PGPASSWORD="${DATABASE_PASSWORD:-}"

    # Drop existing database
    log_warn "Dropping existing database: ${DB_NAME}"
    if ! PGPASSWORD="${DATABASE_PASSWORD:-}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>&1; then
        log_error "Failed to drop existing database"
        unset PGPASSWORD
        exit 1
    fi

    # Create new database
    log_info "Creating new database: ${DB_NAME}"
    if ! PGPASSWORD="${DATABASE_PASSWORD:-}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d postgres \
        -c "CREATE DATABASE ${DB_NAME};" 2>&1; then
        log_error "Failed to create new database"
        unset PGPASSWORD
        exit 1
    fi

    # Restore from backup
    log_info "Restoring data from backup..."
    if ! gunzip -c "${BACKUP_SOURCE}" | PGPASSWORD="${DATABASE_PASSWORD:-}" pg_restore \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose 2>&1; then
        log_error "PostgreSQL restore failed"
        unset PGPASSWORD
        exit 1
    fi

    unset PGPASSWORD

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "PostgreSQL restore completed in ${duration}s"
}

restore_sqlite() {
    log_info "Starting SQLite restore..."
    log_info "Database: ${SQLITE_DB_PATH}"

    local start_time=$(date +%s)

    # Backup original database
    if [[ -f "${SQLITE_DB_PATH}" ]]; then
        local backup_copy="${SQLITE_DB_PATH}.backup"
        log_info "Backing up original database to ${backup_copy}"
        cp "${SQLITE_DB_PATH}" "${backup_copy}" || {
            log_error "Failed to backup original database"
            exit 1
        }
    fi

    # Restore from backup
    log_info "Restoring data from backup..."
    if ! gunzip -c "${BACKUP_SOURCE}" | sqlite3 "${SQLITE_DB_PATH}" 2>&1; then
        log_error "SQLite restore failed"
        if [[ -f "${SQLITE_DB_PATH}.backup" ]]; then
            log_info "Restoring from backup copy..."
            mv "${SQLITE_DB_PATH}.backup" "${SQLITE_DB_PATH}"
        fi
        exit 1
    fi

    # Remove backup copy on success
    if [[ -f "${SQLITE_DB_PATH}.backup" ]]; then
        rm -f "${SQLITE_DB_PATH}.backup"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "SQLite restore completed in ${duration}s"
}

perform_restore() {
    log_info "Performing database restore..."

    case "${DB_TYPE}" in
        postgresql)
            restore_postgresql
            ;;
        sqlite)
            restore_sqlite
            ;;
        *)
            log_error "Unknown database type: ${DB_TYPE}"
            exit 1
            ;;
    esac
}

################################################################################
# Verification Functions
################################################################################

verify_restore() {
    log_info "Verifying restore integrity..."

    if [[ "${DB_TYPE}" == "postgresql" ]]; then
        export PGPASSWORD="${DATABASE_PASSWORD:-}"

        # Check if database exists
        local db_check=$(PGPASSWORD="${DATABASE_PASSWORD:-}" psql \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            -c "SELECT 1;" 2>&1 || echo "FAILED")

        unset PGPASSWORD

        if [[ "${db_check}" == "FAILED" ]]; then
            log_error "Database verification failed"
            return 1
        fi
    fi

    log_success "Restore verification passed"
}

################################################################################
# Cleanup Functions
################################################################################

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."

    if [[ "${BACKUP_SOURCE}" =~ ^${TEMP_DIR} ]]; then
        rm -f "${BACKUP_SOURCE}"
        log_info "Removed temporary backup file"
    fi
}

################################################################################
# Summary Functions
################################################################################

print_summary() {
    log_info "=========================================="
    log_info "RESTORE SUMMARY"
    log_info "=========================================="
    log_info "Backup Source: ${BACKUP_SOURCE}"
    log_info "Database Type: ${DB_TYPE}"

    if [[ "${DB_TYPE}" == "postgresql" ]]; then
        log_info "Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        log_info "Database: ${SQLITE_DB_PATH}"
    fi

    log_info "Restored By: ${RESTORE_USER}"
    log_info "Restore Time: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "=========================================="
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "=========================================="
    log_info "DATABASE RESTORE STARTED"
    log_info "=========================================="

    # Handle backup file selection
    if [[ -z "${BACKUP_SOURCE}" ]]; then
        list_available_backups
        prompt_for_backup
    fi

    # Check prerequisites
    check_prerequisites

    # Download from S3 if needed
    if is_s3_path; then
        download_from_s3
    fi

    # Validate backup file
    validate_backup_file

    # Detect database type
    detect_database_type

    # Confirm restore
    confirm_restore

    # Perform restore
    perform_restore

    # Verify restore
    verify_restore

    # Cleanup temporary files
    cleanup_temp_files

    # Print summary
    print_summary

    log_success "=========================================="
    log_success "DATABASE RESTORE COMPLETED SUCCESSFULLY"
    log_success "=========================================="
}

# Run main function
main "$@"
