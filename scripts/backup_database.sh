#!/bin/bash

################################################################################
# Database Backup Script with S3 Upload Support
#
# Purpose:
#   - Create PostgreSQL or SQLite database backups
#   - Compress backups for storage efficiency
#   - Upload to S3 (optional)
#   - Manage backup retention policy
#   - Provide detailed logging and error handling
#
# Usage:
#   ./backup_database.sh
#
# Environment Variables:
#   DATABASE_HOST        - PostgreSQL host (default: postgres)
#   DATABASE_PORT        - PostgreSQL port (default: 5432)
#   DATABASE_NAME        - Database name (default: socrates)
#   DATABASE_USER        - Database user (default: postgres)
#   DATABASE_PASSWORD    - Database password (required for PostgreSQL)
#   DATABASE_TYPE        - 'postgresql' or 'sqlite' (auto-detect if not set)
#   SQLITE_DB_PATH       - Path to SQLite database file (if using SQLite)
#   BACKUP_DIR           - Local backup directory (default: /backups)
#   S3_BUCKET            - S3 bucket name (optional)
#   S3_PREFIX            - S3 path prefix (default: backups/)
#   AWS_REGION           - AWS region (default: us-east-1)
#   RETENTION_DAYS       - Keep backups for N days (default: 30)
#   COMPRESS_LEVEL       - gzip compression level 1-9 (default: 9)
#   LOG_FILE             - Log file path (default: /var/log/socrates_backup.log)
#
# Examples:
#   # Backup PostgreSQL database
#   DATABASE_HOST=localhost DATABASE_USER=postgres \
#     DATABASE_PASSWORD=secret ./backup_database.sh
#
#   # Backup SQLite with S3 upload
#   DATABASE_TYPE=sqlite SQLITE_DB_PATH=/app/socrates.db \
#     S3_BUCKET=my-backups ./backup_database.sh
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
BACKUP_DIR="${BACKUP_DIR:-/backups}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/}"
AWS_REGION="${AWS_REGION:-us-east-1}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS_LEVEL="${COMPRESS_LEVEL:-9}"
LOG_FILE="${LOG_FILE:-/var/log/socrates_backup.log}"

# Timestamp for backup file naming
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/socrates_${TIMESTAMP}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo -e "${YELLOW}WARNING: $@${NC}" >&2
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}ERROR: $@${NC}" >&2
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

    # Check required commands
    local required_commands=("gzip" "date" "find")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &> /dev/null; then
            log_error "Required command not found: ${cmd}"
            exit 1
        fi
    done

    # Check database-specific commands
    if [[ "${DB_TYPE}" == "postgresql" || -z "${DB_TYPE}" && -z "${SQLITE_DB_PATH}" ]]; then
        if ! command -v pg_dump &> /dev/null; then
            log_error "pg_dump not found. Install PostgreSQL client tools."
            exit 1
        fi
    fi

    # Check S3 tools if S3 upload is enabled
    if [[ -n "${S3_BUCKET}" ]]; then
        if ! command -v aws &> /dev/null; then
            log_error "AWS CLI not found. Install aws-cli for S3 uploads."
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

validate_backup_dir() {
    log_info "Validating backup directory: ${BACKUP_DIR}"

    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log_info "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}" || {
            log_error "Failed to create backup directory"
            exit 1
        }
    fi

    # Check write permissions
    if [[ ! -w "${BACKUP_DIR}" ]]; then
        log_error "No write permission for backup directory: ${BACKUP_DIR}"
        exit 1
    fi

    log_success "Backup directory validated"
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
# Backup Functions
################################################################################

backup_postgresql() {
    log_info "Starting PostgreSQL backup..."
    log_info "Host: ${DB_HOST}, Port: ${DB_PORT}, Database: ${DB_NAME}, User: ${DB_USER}"

    local start_time=$(date +%s)

    # Export password to avoid interactive prompt
    export PGPASSWORD="${DATABASE_PASSWORD:-}"

    # Perform backup using pg_dump with compression
    if ! pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress="${COMPRESS_LEVEL}" \
        --verbose \
        2>&1 | gzip -"${COMPRESS_LEVEL}" > "${BACKUP_FILE}"; then
        log_error "PostgreSQL backup failed"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi

    unset PGPASSWORD

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "PostgreSQL backup completed in ${duration}s"
}

backup_sqlite() {
    log_info "Starting SQLite backup..."
    log_info "Database: ${SQLITE_DB_PATH}"

    if [[ ! -f "${SQLITE_DB_PATH}" ]]; then
        log_error "SQLite database file not found: ${SQLITE_DB_PATH}"
        exit 1
    fi

    local start_time=$(date +%s)

    # Use sqlite3 to dump database, then compress
    if ! sqlite3 "${SQLITE_DB_PATH}" ".dump" 2>&1 | gzip -"${COMPRESS_LEVEL}" > "${BACKUP_FILE}"; then
        log_error "SQLite backup failed"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "SQLite backup completed in ${duration}s"
}

perform_backup() {
    log_info "Performing database backup..."

    case "${DB_TYPE}" in
        postgresql)
            backup_postgresql
            ;;
        sqlite)
            backup_sqlite
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

verify_backup() {
    log_info "Verifying backup integrity..."

    if [[ ! -f "${BACKUP_FILE}" ]]; then
        log_error "Backup file not found: ${BACKUP_FILE}"
        exit 1
    fi

    local file_size=$(du -h "${BACKUP_FILE}" | cut -f1)
    log_info "Backup file size: ${file_size}"

    # Verify gzip integrity
    if ! gzip -t "${BACKUP_FILE}" 2>&1; then
        log_error "Backup file is corrupted or not a valid gzip file"
        rm -f "${BACKUP_FILE}"
        exit 1
    fi

    log_success "Backup verification passed"
}

################################################################################
# S3 Upload Functions
################################################################################

upload_to_s3() {
    if [[ -z "${S3_BUCKET}" ]]; then
        log_info "S3 upload disabled (S3_BUCKET not set)"
        return 0
    fi

    log_info "Uploading backup to S3..."
    log_info "Bucket: ${S3_BUCKET}, Prefix: ${S3_PREFIX}"

    local s3_path="s3://${S3_BUCKET}/${S3_PREFIX}$(basename ${BACKUP_FILE})"

    if ! aws s3 cp "${BACKUP_FILE}" "${s3_path}" \
        --region "${AWS_REGION}" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=${TIMESTAMP},database=${DB_NAME}" \
        --sse AES256 2>&1; then
        log_error "Failed to upload backup to S3"
        return 1
    fi

    log_success "Backup uploaded to S3: ${s3_path}"

    # Generate S3 download link (expires in 7 days)
    local download_url=$(aws s3 presigned-url get-object \
        "s3://${S3_BUCKET}/${S3_PREFIX}$(basename ${BACKUP_FILE})" \
        --expires-in 604800 \
        --region "${AWS_REGION}" 2>/dev/null || echo "N/A")

    log_info "Download link (7 days): ${download_url}"
}

################################################################################
# Retention Management
################################################################################

cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

    local deleted_count=0
    local local_deleted_count=0

    # Delete local backups
    while IFS= read -r file; do
        log_info "Deleting old backup: $(basename ${file})"
        rm -f "${file}"
        ((local_deleted_count++))
    done < <(find "${BACKUP_DIR}" -name "socrates_*.sql.gz" -mtime +${RETENTION_DAYS})

    deleted_count=${local_deleted_count}

    if [[ ${deleted_count} -gt 0 ]]; then
        log_success "Deleted ${deleted_count} old local backup(s)"
    else
        log_info "No old local backups to delete"
    fi

    # Delete S3 backups (if enabled)
    if [[ -n "${S3_BUCKET}" ]]; then
        log_info "Cleaning up S3 backups..."

        local cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)
        local s3_deleted_count=0

        # List and delete old S3 objects
        while IFS= read -r s3_object; do
            if [[ -n "${s3_object}" ]]; then
                log_info "Deleting old S3 backup: ${s3_object}"
                aws s3 rm "s3://${S3_BUCKET}/${s3_object}" --region "${AWS_REGION}" || true
                ((s3_deleted_count++))
            fi
        done < <(aws s3api list-objects-v2 \
            --bucket "${S3_BUCKET}" \
            --prefix "${S3_PREFIX}" \
            --query "Contents[?LastModified<='${cutoff_date}'].Key" \
            --output text \
            --region "${AWS_REGION}" 2>/dev/null || echo "")

        if [[ ${s3_deleted_count} -gt 0 ]]; then
            log_success "Deleted ${s3_deleted_count} old S3 backup(s)"
        fi
    fi
}

################################################################################
# Summary Functions
################################################################################

print_summary() {
    log_info "=========================================="
    log_info "BACKUP SUMMARY"
    log_info "=========================================="
    log_info "Backup File: ${BACKUP_FILE}"
    log_info "File Size: $(du -h ${BACKUP_FILE} | cut -f1)"
    log_info "Timestamp: ${TIMESTAMP}"
    log_info "Database Type: ${DB_TYPE}"

    if [[ "${DB_TYPE}" == "postgresql" ]]; then
        log_info "Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        log_info "Database: ${SQLITE_DB_PATH}"
    fi

    if [[ -n "${S3_BUCKET}" ]]; then
        log_info "S3 Bucket: ${S3_BUCKET}/${S3_PREFIX}"
    fi

    log_info "Retention: ${RETENTION_DAYS} days"
    log_info "=========================================="
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "=========================================="
    log_info "DATABASE BACKUP STARTED"
    log_info "=========================================="

    # Run validation steps
    check_prerequisites
    validate_backup_dir
    detect_database_type

    # Perform backup
    perform_backup

    # Verify backup
    verify_backup

    # Upload to S3
    upload_to_s3

    # Cleanup old backups
    cleanup_old_backups

    # Print summary
    print_summary

    log_success "=========================================="
    log_success "DATABASE BACKUP COMPLETED SUCCESSFULLY"
    log_success "=========================================="
}

# Run main function
main "$@"
