#!/usr/bin/env python3
"""
Socratic RAG Enhanced - System Monitoring Agent
==============================================

System monitoring agent with comprehensive analytics.
Capabilities: Health monitoring, usage tracking, performance analytics
"""

import os
import time
import shutil
from typing import Dict, List, Any, Optional

# Core imports
try:
    from src.core import get_logger, DateTimeHelper, ANTHROPIC_AVAILABLE
    from src.database import get_database
    from .base import BaseAgent, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    get_logger = lambda x: None
    DateTimeHelper = None
    get_database = lambda: None
    BaseAgent = object
    log_agent_action = lambda f: f

# Optional imports with fallbacks
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemMonitorAgent(BaseAgent):
    """
    Enhanced system monitoring agent with comprehensive analytics

    Capabilities: Health monitoring, usage tracking, performance analytics
    """

    def __init__(self):
        super().__init__("system_monitor", "System Monitor")
        self.metrics = {}
        self.start_time = time.time()

    def get_capabilities(self) -> List[str]:
        return [
            "check_health", "track_usage", "monitor_performance", "analyze_costs",
            "generate_analytics", "alert_management", "resource_monitoring",
            "api_usage_tracking", "get_system_stats", "database_health"
        ]

    @log_agent_action
    def _check_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive system health check"""
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        health = {
            'status': 'healthy',
            'timestamp': timestamp,
            'services': {
                'database': self._check_database_health(),
                'claude_api': self._check_claude_api_health(),
                'file_system': self._check_file_system_health(),
                'memory': self._check_memory_usage()
            },
            'performance': self._get_performance_metrics(),
            'alerts': self._get_active_alerts()
        }

        # Overall status based on service health
        service_statuses = [service.get('status') for service in health['services'].values()]
        if 'critical' in service_statuses:
            health['status'] = 'critical'
        elif 'warning' in service_statuses:
            health['status'] = 'warning'

        return health

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

            if not self.db:
                return {
                    'status': 'critical',
                    'error': 'Database service not available',
                    'last_checked': timestamp
                }

            # Use the actual health check from database service
            health_data = self.db.health_check()
            response_time = time.time() - start_time

            # Get basic statistics from repositories
            try:
                project_count = len(self.db.projects.list_all(limit=1000))  # Quick count
                user_count = len(self.db.users.list_all(limit=1000))  # Quick count
            except Exception:
                project_count = 0
                user_count = 0

            return {
                'status': 'healthy' if health_data.get('status') == 'healthy' else 'warning',
                'response_time_ms': round(response_time * 1000, 2),
                'project_count': project_count,
                'user_count': user_count,
                'database_info': health_data.get('database_stats', {}),
                'last_checked': timestamp
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Database health check failed: {e}")
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            return {
                'status': 'critical',
                'error': str(e),
                'last_checked': timestamp
            }

    def _check_claude_api_health(self) -> Dict[str, Any]:
        """Check Claude API connectivity and quota"""
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        if not ANTHROPIC_AVAILABLE:
            return {
                'status': 'unavailable',
                'message': 'Anthropic package not installed',
                'last_checked': timestamp
            }

        if not self.claude_client:
            return {
                'status': 'unavailable',
                'message': 'Claude API not configured',
                'last_checked': timestamp
            }

        try:
            # Simple test call with minimal tokens
            start_time = time.time()
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "test"}]
            )
            response_time = time.time() - start_time

            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'model': 'claude-3-haiku-20240307',
                'last_checked': timestamp
            }

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Claude API health check failed: {e}")
            return {
                'status': 'warning',
                'error': str(e),
                'last_checked': timestamp
            }

    def _check_file_system_health(self) -> Dict[str, Any]:
        """Check file system availability and space"""
        try:
            # Get data directory from config
            data_dir = self.config.get('system.data_path', 'data') if self.config else 'data'

            # Ensure data directory exists
            os.makedirs(data_dir, exist_ok=True)

            total, used, free = shutil.disk_usage(data_dir)

            # Calculate usage percentage
            usage_percent = (used / total) * 100

            # Determine status based on free space
            if free < 100 * 1024 ** 2:  # Less than 100MB
                status = 'critical'
            elif free < 1024 ** 3:  # Less than 1GB
                status = 'warning'
            else:
                status = 'healthy'

            return {
                'status': status,
                'data_dir': data_dir,
                'total_gb': round(total / 1024 ** 3, 2),
                'used_gb': round(used / 1024 ** 3, 2),
                'free_gb': round(free / 1024 ** 3, 2),
                'usage_percentage': round(usage_percent, 1)
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"File system health check failed: {e}")
            return {
                'status': 'warning',
                'error': str(e)
            }

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage"""
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'unavailable',
                'message': 'psutil not available for memory monitoring'
            }

        try:
            memory = psutil.virtual_memory()

            # Determine status based on memory usage
            if memory.percent > 90:
                status = 'critical'
            elif memory.percent > 80:
                status = 'warning'
            else:
                status = 'healthy'

            return {
                'status': status,
                'total_gb': round(memory.total / 1024 ** 3, 2),
                'available_gb': round(memory.available / 1024 ** 3, 2),
                'used_percentage': round(memory.percent, 1),
                'free_gb': round((memory.total - memory.used) / 1024 ** 3, 2)
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Memory usage check failed: {e}")
            return {
                'status': 'warning',
                'error': str(e)
            }

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get basic performance metrics"""
        uptime_seconds = time.time() - self.start_time

        metrics = {
            'uptime_seconds': round(uptime_seconds, 1),
            'uptime_formatted': self._format_uptime(uptime_seconds)
        }

        # Add CPU info if available
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                metrics.update({
                    'cpu_usage_percent': round(cpu_percent, 1),
                    'cpu_count': psutil.cpu_count()
                })
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"CPU metrics unavailable: {e}")

        return metrics

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts = []

        try:
            # Get basic statistics from database repositories
            if self.db:
                project_count = len(self.db.projects.list_all(limit=200))

                # Alert if too many projects
                if project_count > 100:
                    alerts.append({
                        'type': 'capacity_warning',
                        'message': f'High number of projects ({project_count}) may impact performance',
                        'severity': 'medium',
                        'count': project_count
                    })

                # Check for generated files
                try:
                    files_count = len(self.db.generated_files.list_all(limit=1500))
                    if files_count > 1000:
                        alerts.append({
                            'type': 'storage_warning',
                            'message': f'Many generated files ({files_count}) may consume storage',
                            'severity': 'low',
                            'count': files_count
                        })
                except Exception:
                    # generated_files repository might not be available
                    pass

        except Exception as e:
            alerts.append({
                'type': 'monitoring_error',
                'message': f'Statistics monitoring failed: {str(e)}',
                'severity': 'low'
            })

        # Check for Claude API issues
        if ANTHROPIC_AVAILABLE and not self.claude_client:
            alerts.append({
                'type': 'service_warning',
                'message': 'Claude API not configured - some features unavailable',
                'severity': 'medium'
            })

        return alerts

    @log_agent_action
    def _get_system_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

            # Get basic statistics from repositories
            stats = self._get_database_stats()

            # Get health information
            health = self._check_health({})

            # Combine all stats
            system_stats = {
                'timestamp': timestamp,
                'database_stats': stats,
                'health_summary': {
                    'overall_status': health['status'],
                    'services_healthy': sum(1 for s in health['services'].values() if s.get('status') == 'healthy'),
                    'services_total': len(health['services']),
                    'alerts_count': len(health['alerts'])
                },
                'performance': health['performance'],
                'uptime': health['performance']['uptime_formatted']
            }

            return system_stats

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get system stats: {e}")
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            return {
                'error': str(e),
                'timestamp': timestamp
            }

    def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics using actual repository methods"""
        stats = {
            'users_count': 0,
            'projects_count': 0,
            'modules_count': 0,
            'generated_files_count': 0,
            'test_results_count': 0
        }

        if not self.db:
            return stats

        try:
            # Get counts from repositories (limited to avoid performance issues)
            stats['users_count'] = len(self.db.users.list_all(limit=1000))
            stats['projects_count'] = len(self.db.projects.list_all(limit=1000))

            try:
                stats['modules_count'] = len(self.db.modules.list_all(limit=1000))
            except Exception:
                pass  # modules repository might not be available

            try:
                stats['generated_files_count'] = len(self.db.generated_files.list_all(limit=1500))
            except Exception:
                pass  # generated_files repository might not be available

            try:
                stats['test_results_count'] = len(self.db.test_results.list_all(limit=1500))
            except Exception:
                pass  # test_results repository might not be available

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to get database stats: {e}")

        return stats

    @log_agent_action
    def _track_usage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track system usage and generate analytics"""
        period = data.get('period', '24h')  # 1h, 24h, 7d, 30d
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        try:
            # Get database statistics
            db_stats = self._get_database_stats()

            usage_stats = {
                'period': period,
                'timestamp': timestamp,
                'database_usage': db_stats,
                'api_usage': self._get_api_usage_stats(period),
                'user_activity': self._get_user_activity_stats(db_stats),
                'project_activity': self._get_project_activity_stats(db_stats),
                'system_performance': self._get_system_performance_stats()
            }

            return usage_stats

        except Exception as e:
            if self.logger:
                self.logger.error(f"Usage tracking failed: {e}")
            return {
                'error': str(e),
                'period': period,
                'timestamp': timestamp
            }

    def _get_api_usage_stats(self, period: str) -> Dict[str, Any]:
        """Get Claude API usage statistics"""
        # Simplified - in real implementation would track actual usage
        return {
            'period': period,
            'total_requests': 0,  # Would track actual requests
            'total_tokens': 0,  # Would track actual tokens
            'estimated_cost_usd': 0.0,
            'average_response_time_ms': 0,
            'error_rate_percentage': 0.0,
            'available': ANTHROPIC_AVAILABLE and self.claude_client is not None
        }

    def _get_user_activity_stats(self, db_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Get user activity statistics"""
        return {
            'total_users': db_stats.get('users_count', 0),
            'active_users_estimate': max(1, db_stats.get('users_count', 0) // 2),  # Simplified
            'new_users_estimate': 0,  # Would track actual new users
            'login_count_estimate': 0  # Would track actual logins
        }

    def _get_project_activity_stats(self, db_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Get project activity statistics"""
        return {
            'total_projects': db_stats.get('projects_count', 0),
            'active_projects': db_stats.get('projects_count', 0),  # Simplified
            'archived_projects': 0,  # Would check project status
            'files_generated': db_stats.get('generated_files_count', 0),
            'tests_run': db_stats.get('test_results_count', 0),
            'modules_created': db_stats.get('modules_count', 0)
        }

    def _get_system_performance_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        perf_stats = {
            'uptime_seconds': time.time() - self.start_time,
            'memory_available': PSUTIL_AVAILABLE,
            'claude_api_available': ANTHROPIC_AVAILABLE and self.claude_client is not None
        }

        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=0.1)

                perf_stats.update({
                    'memory_usage_percent': round(memory.percent, 1),
                    'cpu_usage_percent': round(cpu_percent, 1)
                })
            except Exception as e:
                perf_stats['performance_error'] = str(e)

        return perf_stats

    @log_agent_action
    def _database_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed database health and statistics"""
        try:
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

            # Get comprehensive database health info
            health = self.db.health_check() if self.db else {'status': 'unavailable'}
            stats = self._get_database_stats()

            # Calculate some derived metrics
            total_entities = sum(
                stats.get(key, 0)
                for key in ['projects_count', 'users_count', 'modules_count', 'generated_files_count']
            )

            db_health = {
                'connection_status': health.get('status', 'unknown'),
                'response_time': 'See health check for timing',
                'statistics': stats,
                'total_entities': total_entities,
                'database_info': health.get('database_stats', {}),
                'recommendations': [],
                'timestamp': timestamp
            }

            # Add recommendations based on stats
            if stats.get('projects_count', 0) > 50:
                db_health['recommendations'].append("Consider archiving old projects")

            if stats.get('generated_files_count', 0) > 500:
                db_health['recommendations'].append("Monitor file storage usage")

            return db_health

        except Exception as e:
            if self.logger:
                self.logger.error(f"Database health check failed: {e}")
            timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None
            return {
                'connection_status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }

    @log_agent_action
    def _generate_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        report_type = data.get('type', 'summary')  # summary, detailed, performance
        time_range = data.get('time_range', '7d')
        timestamp = DateTimeHelper.to_iso_string(DateTimeHelper.now()) if DateTimeHelper else None

        try:
            base_analytics = {
                'report_type': report_type,
                'time_range': time_range,
                'generated_at': timestamp,
                'system_health': self._check_health({}),
                'usage_stats': self._track_usage({'period': time_range})
            }

            if report_type == 'detailed':
                base_analytics.update({
                    'database_health': self._database_health({}),
                    'performance_trends': self._get_performance_trends(),
                    'capacity_analysis': self._analyze_capacity()
                })

            return base_analytics

        except Exception as e:
            if self.logger:
                self.logger.error(f"Analytics generation failed: {e}")
            return {
                'error': str(e),
                'report_type': report_type,
                'generated_at': timestamp
            }

    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends over time"""
        # Simplified - in real implementation would track historical data
        return {
            'trend': 'stable',
            'note': 'Performance trending not implemented - would track historical metrics'
        }

    def _analyze_capacity(self) -> Dict[str, Any]:
        """Analyze system capacity and usage"""
        try:
            stats = self._get_database_stats()

            # Simple capacity analysis
            capacity = {
                'database_load': 'light',  # Would calculate based on actual metrics
                'storage_usage': 'normal',
                'memory_pressure': 'low',
                'recommendations': []
            }

            # Add recommendations based on current stats
            if stats.get('projects_count', 0) > 75:
                capacity['database_load'] = 'moderate'
                capacity['recommendations'].append("Monitor database performance")

            if stats.get('generated_files_count', 0) > 750:
                capacity['storage_usage'] = 'high'
                capacity['recommendations'].append("Consider file cleanup policies")

            return capacity

        except Exception as e:
            return {
                'error': str(e),
                'analysis': 'unavailable'
            }
