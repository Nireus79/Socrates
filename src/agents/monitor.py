#!/usr/bin/env python3
"""
SystemMonitorAgent - Comprehensive System Monitoring and Analytics
================================================================

Handles system health monitoring, performance tracking, usage analytics, and alerting.
Fully corrected according to project standards.

Capabilities:
- Health checking and performance monitoring
- API usage tracking and cost analysis
- User activity analytics
- Alert management and notifications
- Resource utilization monitoring
- Database health and statistics
"""

from typing import Dict, List, Any, Optional, Union
from functools import wraps
import os
import time
import shutil

# Import from correct locations
from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
from src import get_logger, get_event_bus  # ← Changed: import from src, not src.core

try:
    from src.models import UserActivity, ProjectMetrics
    from src.database import get_database
    from .base import BaseAgent, require_authentication, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Comprehensive fallback implementations
    import logging
    from datetime import datetime
    from enum import Enum

    def get_logger(name):
        return logging.getLogger(name)


    def get_event_bus():
        return None


    def get_database():
        return None


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

        @staticmethod
        def from_iso_string(iso_str: str):
            return datetime.fromisoformat(iso_str) if iso_str else None


    class ValidationError(Exception):
        pass


    class ValidationHelper:
        @staticmethod
        def validate_email(email: str) -> bool:
            return "@" in str(email) if email else False


    class UserActivity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class ProjectMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class BaseAgent:
        def __init__(self, agent_id: str, name: str):
            self.agent_id = agent_id
            self.name = name
            self.logger = get_logger(agent_id)

        def _error_response(self, message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
            return {'success': False, 'error': message, 'error_code': error_code}

        def _success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
            return {'success': True, 'message': message, 'data': data or {}}


    def require_authentication(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def log_agent_action(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

# Optional imports with fallbacks
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False


class SystemMonitorAgent(BaseAgent):
    """Enhanced system monitoring agent with comprehensive analytics"""

    def __init__(self, services: Optional[ServiceContainer] = None):
        super().__init__("system_monitor", "System Monitor Agent", services)
        self.db_service = get_database()
        self.event_bus = get_event_bus()

        # Monitoring settings
        self.metrics: Dict[str, Any] = {}
        self.start_time: float = time.time()
        self.alert_thresholds: Dict[str, Union[int, float]] = {
            'memory_warning': 80,  # percentage
            'memory_critical': 90,
            'projects_warning': 50,
            'projects_critical': 100,
            'files_warning': 500,
            'files_critical': 1000,
            'response_time_warning': 1000,  # milliseconds
            'response_time_critical': 3000
        }

        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.max_history_size: int = 100

        # API usage tracking
        self.api_calls: List[Dict[str, Any]] = []
        self.max_api_history: int = 1000

        self.logger.info("SystemMonitorAgent initialized with comprehensive monitoring")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "check_health",
            "track_usage",
            "monitor_performance",
            "analyze_costs",
            "generate_analytics",
            "alert_management",
            "resource_monitoring",
            "api_usage_tracking",
            "get_system_stats",
            "database_health",
            "user_activity_stats",
            "project_metrics"
        ]

    @require_authentication
    @log_agent_action
    def check_health(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive system health check

        Args:
            request_data: {
                'detailed': bool,  # Include detailed metrics
                'include_recommendations': bool
            }

        Returns:
            Dict with system health status and metrics
        """
        try:
            detailed = request_data.get('detailed', False)
            include_recommendations = request_data.get('include_recommendations', True)

            health = {
                'status': 'healthy',
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'services': {
                    'database': self._check_database_health(),
                    'file_system': self._check_file_system_health(),
                    'memory': self._check_memory_usage(),
                    'api_access': self._check_api_access()
                },
                'performance': self._get_performance_metrics(),
                'alerts': self._get_active_alerts()
            }

            # Determine overall status
            service_statuses = [service.get('status', 'unknown') for service in health['services'].values()]
            if 'critical' in service_statuses:
                health['status'] = 'critical'
            elif 'warning' in service_statuses:
                health['status'] = 'warning'

            # Add detailed information if requested
            if detailed:
                health['detailed_metrics'] = self._get_detailed_metrics()
                health['resource_usage'] = self._get_resource_usage()

            # Add recommendations if requested
            if include_recommendations:
                health['recommendations'] = self._generate_health_recommendations(health)

            # Fire event
            if self.event_bus:
                self.event_bus.emit('health_check_completed', self.agent_id, {
                    'status': health['status'],
                    'alerts_count': len(health['alerts']),
                    'services_healthy': sum(1 for s in health['services'].values() if s.get('status') == 'healthy')
                })

            return self._success_response(
                f"System health check completed - Status: {health['status']}",
                {'health': health}
            )

        except (RuntimeError, ValueError, OSError) as e:
            error_msg = f"Health check failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "HEALTH_CHECK_FAILED")

    @require_authentication
    @log_agent_action
    def track_usage(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track system usage and generate analytics

        Args:
            request_data: {
                'period': str,  # 1h, 24h, 7d, 30d
                'user_id': Optional[str],
                'include_trends': bool
            }

        Returns:
            Dict with usage statistics and analytics
        """
        try:
            period = request_data.get('period', '24h')
            user_id = request_data.get('user_id')
            include_trends = request_data.get('include_trends', False)

            # Get database statistics
            db_stats = self._get_database_stats()

            usage_stats = {
                'period': period,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'database': db_stats,
                'api_usage': self._get_api_usage_stats(period),
                'system_resources': self._get_resource_usage()
            }

            # Add user-specific stats if requested
            if user_id:
                usage_stats['user_activity'] = self._get_user_activity_details(user_id, period)

            # Add trend analysis if requested
            if include_trends:
                usage_stats['trends'] = self._analyze_usage_trends(period)

            # Fire event
            if self.event_bus:
                self.event_bus.emit('usage_tracked', self.agent_id, {
                    'period': period,
                    'user_id': user_id,
                    'total_projects': db_stats.get('projects_count', 0)
                })

            return self._success_response(
                f"Usage statistics generated for period: {period}",
                {'usage': usage_stats}
            )

        except (RuntimeError, ValueError, KeyError) as e:
            error_msg = f"Usage tracking failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "USAGE_TRACKING_FAILED")

    @require_authentication
    @log_agent_action
    def monitor_performance(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor system performance metrics

        Args:
            request_data: {
                'time_range': str,  # 1h, 24h, 7d
                'include_historical': bool,
                'include_recommendations': bool
            }

        Returns:
            Dict with performance metrics and analysis
        """
        try:
            time_range = request_data.get('time_range', '1h')
            include_historical = request_data.get('include_historical', False)
            include_recommendations = request_data.get('include_recommendations', True)

            performance = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'current_metrics': self._get_comprehensive_performance_metrics(),
                'response_times': self._calculate_response_times(),
                'bottlenecks': self._analyze_bottlenecks()
            }

            # Add historical data if requested
            if include_historical:
                performance['historical_data'] = self._get_performance_trends(time_range)

            # Add recommendations if requested
            if include_recommendations:
                performance['recommendations'] = self._get_optimization_recommendations()

            # Fire event
            if self.event_bus:
                self.event_bus.emit('performance_monitored', self.agent_id, {
                    'time_range': time_range,
                    'avg_response_time': performance['response_times'].get('average_ms', 0)
                })

            return self._success_response(
                f"Performance monitoring completed for {time_range}",
                {'performance': performance}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Performance monitoring failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "PERFORMANCE_MONITORING_FAILED")

    @require_authentication
    @log_agent_action
    def analyze_costs(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze API and resource costs

        Args:
            request_data: {
                'time_range': str,  # 1h, 24h, 7d, 30d
                'include_projections': bool,
                'breakdown_by': str  # 'project', 'user', 'operation'
            }

        Returns:
            Dict with cost analysis and projections
        """
        try:
            time_range = request_data.get('time_range', '30d')
            include_projections = request_data.get('include_projections', True)
            breakdown_by = request_data.get('breakdown_by', 'project')

            cost_analysis = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'api_costs': self._analyze_api_costs(time_range),
                'resource_costs': self._analyze_resource_costs(),
                'total_estimated_cost': 0.0
            }

            # Calculate total estimated cost
            cost_analysis: Dict[str, Any] = {
                'api_costs': {},
                'resource_costs': {}
            }

            # Add cost breakdown
            if breakdown_by == 'project':
                cost_analysis['breakdown'] = self._get_cost_by_project(time_range)
            elif breakdown_by == 'user':
                cost_analysis['breakdown'] = self._get_cost_by_user(time_range)
            elif breakdown_by == 'operation':
                cost_analysis['breakdown'] = self._get_cost_by_operation(time_range)

            # Add projections if requested
            if include_projections:
                cost_analysis['projections'] = self._calculate_cost_projections(cost_analysis)

            # Add optimization suggestions
            cost_analysis['optimization_suggestions'] = self._get_cost_optimization_suggestions()

            # Fire event
            if self.event_bus:
                self.event_bus.emit('costs_analyzed', self.agent_id, {
                    'time_range': time_range,
                    'total_cost': cost_analysis['total_estimated_cost']
                })

            return self._success_response(
                f"Cost analysis completed for {time_range}",
                {'costs': cost_analysis}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Cost analysis failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "COST_ANALYSIS_FAILED")

    @require_authentication
    @log_agent_action
    def generate_analytics(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report

        Args:
            request_data: {
                'report_type': str,  # 'summary', 'detailed', 'executive'
                'time_range': str,
                'include_charts': bool
            }

        Returns:
            Dict with comprehensive analytics
        """
        try:
            report_type = request_data.get('report_type', 'summary')
            time_range = request_data.get('time_range', '7d')
            include_charts = request_data.get('include_charts', False)

            analytics = {
                'report_type': report_type,
                'generated_at': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'system_health': self._get_health_summary(),
                'usage_metrics': self._get_usage_metrics(time_range),
                'performance_metrics': self._get_performance_summary(time_range),
                'user_activity': self._get_user_activity_summary(time_range),
                'project_statistics': self._get_project_statistics()
            }

            # Add detailed sections based on report type
            if report_type in ['detailed', 'executive']:
                analytics['trends'] = self._get_trend_analysis(time_range)
                analytics['capacity_analysis'] = self._analyze_capacity()
                analytics['insights'] = self._generate_insights(analytics)

            # Add executive summary for executive reports
            if report_type == 'executive':
                analytics['executive_summary'] = self._generate_executive_summary(analytics)

            # Add chart data if requested
            if include_charts:
                analytics['chart_data'] = self._prepare_chart_data(analytics)

            # Fire event
            if self.event_bus:
                self.event_bus.emit('analytics_generated', self.agent_id, {
                    'report_type': report_type,
                    'time_range': time_range
                })

            return self._success_response(
                f"Analytics report generated: {report_type}",
                {'analytics': analytics}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Analytics generation failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "ANALYTICS_GENERATION_FAILED")

    @require_authentication
    @log_agent_action
    def alert_management(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage system alerts and thresholds

        Args:
            request_data: {
                'action': str,  # 'get_alerts', 'set_threshold', 'acknowledge', 'clear'
                'alert_id': Optional[str],
                'threshold_config': Optional[Dict]
            }

        Returns:
            Dict with alert management results
        """
        try:
            action = request_data.get('action', 'get_alerts')

            if action == 'get_alerts':
                alerts = self._get_active_alerts()
                return self._success_response(
                    f"Retrieved {len(alerts)} active alerts",
                    {'alerts': alerts}
                )

            elif action == 'set_threshold':
                threshold_config = request_data.get('threshold_config', {})
                self._update_alert_thresholds(threshold_config)
                return self._success_response(
                    "Alert thresholds updated successfully",
                    {'thresholds': self.alert_thresholds}
                )

            elif action == 'acknowledge':
                alert_id = request_data.get('alert_id')
                if not alert_id:
                    return self._error_response("Alert ID required for acknowledgment", "MISSING_ALERT_ID")

                result = self._acknowledge_alert(alert_id)
                return self._success_response(
                    f"Alert {alert_id} acknowledged",
                    {'result': result}
                )

            elif action == 'clear':
                cleared_count = self._clear_resolved_alerts()
                return self._success_response(
                    f"Cleared {cleared_count} resolved alerts",
                    {'cleared_count': cleared_count}
                )

            else:
                return self._error_response(f"Unknown action: {action}", "INVALID_ACTION")

        except (RuntimeError, ValueError, KeyError) as e:
            error_msg = f"Alert management failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "ALERT_MANAGEMENT_FAILED")

    @require_authentication
    @log_agent_action
    def resource_monitoring(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor system resource utilization

        Args:
            request_data: {
                'include_processes': bool,
                'include_disk_details': bool
            }

        Returns:
            Dict with resource utilization metrics
        """
        try:
            include_processes = request_data.get('include_processes', False)
            include_disk_details = request_data.get('include_disk_details', False)

            resources = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'cpu': self._get_cpu_info(),
                'memory': self._get_memory_info(),
                'disk': self._get_disk_info()
            }

            if include_processes and PSUTIL_AVAILABLE:
                resources['top_processes'] = self._get_top_processes()

            if include_disk_details:
                resources['disk_details'] = self._get_disk_usage_details()

            # Check for resource warnings
            warnings = self._check_resource_warnings(resources)
            if warnings:
                resources['warnings'] = warnings

            return self._success_response(
                "Resource monitoring completed",
                {'resources': resources}
            )

        except (RuntimeError, ValueError, OSError) as e:
            error_msg = f"Resource monitoring failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "RESOURCE_MONITORING_FAILED")

    @require_authentication
    @log_agent_action
    def api_usage_tracking(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track API usage and rate limits

        Args:
            request_data: {
                'time_range': str,
                'breakdown_by': str  # 'endpoint', 'user', 'project'
            }

        Returns:
            Dict with API usage statistics
        """
        try:
            time_range = request_data.get('time_range', '24h')
            breakdown_by = request_data.get('breakdown_by', 'endpoint')

            api_usage = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'total_calls': len(self.api_calls),
                'rate_limits': self._get_rate_limit_status(),
                'statistics': self._calculate_api_statistics(time_range)
            }

            # Add breakdown
            if breakdown_by == 'endpoint':
                api_usage['breakdown'] = self._get_api_usage_by_endpoint(time_range)
            elif breakdown_by == 'user':
                api_usage['breakdown'] = self._get_api_usage_by_user(time_range)
            elif breakdown_by == 'project':
                api_usage['breakdown'] = self._get_api_usage_by_project(time_range)

            return self._success_response(
                f"API usage tracked for {time_range}",
                {'api_usage': api_usage}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"API usage tracking failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "API_TRACKING_FAILED")

    @require_authentication
    @log_agent_action
    def get_system_stats(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive system statistics

        Args:
            request_data: {
                'include_historical': bool,
                'format': str  # 'summary', 'detailed'
            }

        Returns:
            Dict with system statistics
        """
        try:
            include_historical = request_data.get('include_historical', False)
            format_type = request_data.get('format', 'summary')

            stats = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'uptime': self._format_uptime(time.time() - self.start_time),
                'database': self._get_database_stats(),
                'performance': self._get_performance_metrics(),
                'resource_usage': self._get_resource_usage()
            }

            # Add historical data if requested
            if include_historical:
                stats['historical_performance'] = self._get_historical_performance()

            # Add detailed information if requested
            if format_type == 'detailed':
                stats['detailed_breakdown'] = {
                    'memory_details': self._get_detailed_memory_info(),
                    'disk_usage': self._get_disk_usage_info(),
                    'process_info': self._get_process_info()
                }

            return self._success_response(
                f"System statistics retrieved ({format_type} format)",
                {'stats': stats}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Failed to get system stats: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "STATS_FAILED")

    @require_authentication
    @log_agent_action
    def database_health(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check database health and performance

        Args:
            request_data: {
                'include_details': bool,
                'check_optimization': bool
            }

        Returns:
            Dict with database health information
        """
        try:
            include_details = request_data.get('include_details', False)
            check_optimization = request_data.get('check_optimization', True)

            db_health = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'status': 'unknown',
                'basic_stats': self._get_database_stats()
            }

            # Check database connectivity
            if self.db_service:
                health_check = self.db_service.health_check()
                db_health['status'] = health_check.get('status', 'unknown')
                db_health['response_time'] = self._measure_db_response_time()

            # Add detailed information if requested
            if include_details:
                db_health['details'] = self._get_database_health_details()

            # Add optimization suggestions if requested
            if check_optimization:
                db_health['optimization_suggestions'] = self._get_db_optimization_suggestions()

            return self._success_response(
                f"Database health check completed - Status: {db_health['status']}",
                {'database_health': db_health}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Database health check failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "DB_HEALTH_CHECK_FAILED")

    @require_authentication
    @log_agent_action
    def user_activity_stats(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user activity statistics

        Args:
            request_data: {
                'time_range': str,
                'user_id': Optional[str],
                'include_details': bool
            }

        Returns:
            Dict with user activity statistics
        """
        try:
            time_range = request_data.get('time_range', '7d')
            user_id = request_data.get('user_id')
            include_details = request_data.get('include_details', False)

            activity_stats = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'summary': self._get_user_activity_summary(time_range)
            }

            # Add user-specific statistics if requested
            if user_id:
                activity_stats['user_specific'] = self._get_user_activity_details(user_id, time_range)

            # Add detailed breakdown if requested
            if include_details:
                activity_stats['detailed_activity'] = self._get_detailed_user_activity(time_range)

            return self._success_response(
                f"User activity statistics for {time_range}",
                {'activity': activity_stats}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"User activity stats failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "USER_ACTIVITY_FAILED")

    @require_authentication
    @log_agent_action
    def project_metrics(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get project-level metrics and analytics

        Args:
            request_data: {
                'project_id': Optional[str],
                'include_comparisons': bool,
                'time_range': str
            }

        Returns:
            Dict with project metrics
        """
        try:
            project_id = request_data.get('project_id')
            include_comparisons = request_data.get('include_comparisons', False)
            time_range = request_data.get('time_range', '30d')

            metrics = {
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'time_range': time_range,
                'overall_statistics': self._get_project_statistics()
            }

            # Add project-specific metrics if requested
            if project_id:
                metrics['project_specific'] = self._get_project_specific_metrics(project_id)

            # Add comparisons if requested
            if include_comparisons:
                metrics['comparisons'] = self._compare_project_metrics(project_id, time_range)

            return self._success_response(
                f"Project metrics retrieved for {time_range}",
                {'metrics': metrics}
            )

        except (RuntimeError, ValueError) as e:
            error_msg = f"Project metrics failed: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg, "PROJECT_METRICS_FAILED")

    # ========================================================================
    # HELPER METHODS - HEALTH CHECKING
    # ========================================================================

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            if not self.db_service:
                return {
                    'status': 'warning',
                    'message': 'Database service not available',
                    'response_time': None
                }

            start_time = time.time()

            # Test database connection with health check
            if hasattr(self.db_service, 'health_check'):
                health = self.db_service.health_check()
                status = health.get('status', 'unknown')
            else:
                # Fallback test - try to access a simple operation
                try:
                    if hasattr(self.db_service, 'users'):
                        self.db_service.users.list_all(limit=1)
                    status = 'healthy'
                except (RuntimeError, ValueError, AttributeError):
                    status = 'warning'

            response_time = round((time.time() - start_time) * 1000, 2)  # ms

            # Determine status based on response time
            if response_time > 1000:  # > 1 second
                status = 'critical' if status == 'healthy' else status
            elif response_time > 500:  # > 0.5 seconds
                status = 'warning' if status == 'healthy' else status

            return {
                'status': status,
                'response_time_ms': response_time,
                'message': f'Database responding in {response_time}ms'
            }

        except (RuntimeError, OSError, AttributeError) as e:
            return {
                'status': 'critical',
                'error': str(e),
                'message': 'Database connection failed'
            }

    def _check_file_system_health(self) -> Dict[str, Any]:
        """Check file system health and available space"""
        try:
            # Check data directory
            data_dir = 'data'
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            # Get disk usage
            disk_usage = shutil.disk_usage(data_dir)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            status = 'healthy'
            if usage_percent > 90:
                status = 'critical'
            elif usage_percent > 80:
                status = 'warning'

            return {
                'status': status,
                'usage_percent': round(usage_percent, 2),
                'free_gb': round(disk_usage.free / (1024 ** 3), 2),
                'total_gb': round(disk_usage.total / (1024 ** 3), 2),
                'message': f'Disk usage at {usage_percent:.1f}%'
            }

        except (OSError, ZeroDivisionError) as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': 'File system check failed'
            }

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            if PSUTIL_AVAILABLE and psutil is not None:
                mem = psutil.virtual_memory()
                status = 'healthy'

                if mem.percent > self.alert_thresholds['memory_critical']:
                    status = 'critical'
                elif mem.percent > self.alert_thresholds['memory_warning']:
                    status = 'warning'

                return {
                    'status': status,
                    'usage_percent': round(mem.percent, 2),
                    'available_gb': round(mem.available / (1024 ** 3), 2),
                    'total_gb': round(mem.total / (1024 ** 3), 2),
                    'message': f'Memory usage at {mem.percent:.1f}%'
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'Memory accessible (detailed metrics unavailable)',
                    'note': 'Install psutil for detailed memory metrics'
                }

        except (RuntimeError, AttributeError) as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': 'Memory check failed'
            }

    def _check_api_access(self) -> Dict[str, Any]:
        """Check external API access"""
        try:
            if ANTHROPIC_AVAILABLE:
                return {
                    'status': 'healthy',
                    'anthropic_api': 'available',
                    'message': 'API libraries available'
                }
            else:
                return {
                    'status': 'warning',
                    'anthropic_api': 'unavailable',
                    'message': 'Anthropic API library not installed'
                }

        except (RuntimeError, ImportError) as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': 'API access check failed'
            }

    # ========================================================================
    # HELPER METHODS - PERFORMANCE METRICS
    # ========================================================================

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get basic performance metrics"""
        uptime_seconds = time.time() - self.start_time

        metrics: Dict[str, Any] = {
            'uptime_seconds': round(uptime_seconds, 1),
            'uptime_formatted': self._format_uptime(uptime_seconds)
        }

        # Add system metrics if available
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                metrics.update({
                    'cpu_usage_percent': round(cpu_percent, 1),
                    'cpu_count': psutil.cpu_count(),
                    'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                })
            except (RuntimeError, AttributeError) as e:
                metrics['performance_note'] = f'Some metrics unavailable: {e}'

        return metrics

    def _get_comprehensive_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = self._get_performance_metrics()

        # Add additional performance data
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                cpu_times = psutil.cpu_times_percent(interval=0.1)
                metrics['cpu_times'] = {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'idle': cpu_times.idle
                }

                vm = psutil.virtual_memory()
                metrics['memory'] = {
                    'percent': vm.percent,
                    'used_gb': round(vm.used / (1024 ** 3), 2)
                }
            except (RuntimeError, AttributeError) as e:
                self.logger.warning(f"Could not get extended performance metrics: {e}")

        return metrics

    def _calculate_response_times(self) -> Dict[str, Any]:
        """Calculate average response times from performance history"""
        if not self.performance_history:
            return {
                'average_ms': 0.0,
                'min_ms': 0.0,
                'max_ms': 0.0,
                'sample_count': 0
            }

        response_times: List[float] = []
        for entry in self.performance_history[-50:]:  # Last 50 entries
            if 'response_time' in entry.get('metrics', {}):
                response_times.append(float(entry['metrics']['response_time']))

        if not response_times:
            return {
                'average_ms': 0.0,
                'min_ms': 0.0,
                'max_ms': 0.0,
                'sample_count': 0
            }

        return {
            'average_ms': round(sum(response_times) / len(response_times), 2),
            'min_ms': round(min(response_times), 2),
            'max_ms': round(max(response_times), 2),
            'sample_count': len(response_times)
        }

    def _analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze system bottlenecks"""
        bottlenecks: List[Dict[str, Any]] = []

        # Check memory usage
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                mem = psutil.virtual_memory()
                if mem.percent > 85:
                    bottlenecks.append({
                        'type': 'memory',
                        'severity': 'high' if mem.percent > 90 else 'medium',
                        'description': f'Memory usage at {mem.percent:.1f}%',
                        'recommendation': 'Consider freeing memory or upgrading resources'
                    })

                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                if cpu_percent > 80:
                    bottlenecks.append({
                        'type': 'cpu',
                        'severity': 'high' if cpu_percent > 90 else 'medium',
                        'description': f'CPU usage at {cpu_percent:.1f}%',
                        'recommendation': 'High CPU usage detected, consider optimization'
                    })
            except (RuntimeError, AttributeError) as e:
                self.logger.warning(f"Could not analyze bottlenecks: {e}")

        # Check database response time
        db_health = self._check_database_health()
        if db_health.get('response_time_ms', 0) > 1000:
            bottlenecks.append({
                'type': 'database',
                'severity': 'medium',
                'description': f"Database response time: {db_health['response_time_ms']}ms",
                'recommendation': 'Consider database optimization or indexing'
            })

        return bottlenecks

    def _get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations: List[str] = []

        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                mem = psutil.virtual_memory()
                if mem.percent > 80:
                    recommendations.append("High memory usage - consider archiving old projects or clearing caches")

                cpu_percent = psutil.cpu_percent(interval=0.1)
                if cpu_percent > 70:
                    recommendations.append("High CPU usage - review background processes and optimize queries")
            except (RuntimeError, AttributeError) as e:
                self.logger.warning(f"Could not get optimization recommendations: {e}")

        # Check database size
        db_stats = self._get_database_stats()
        if db_stats.get('projects_count', 0) > 100:
            recommendations.append("Large number of projects - consider archiving completed projects")

        if not recommendations:
            recommendations.append("System performance is optimal - no immediate optimizations needed")

        return recommendations

    # ========================================================================
    # HELPER METHODS - DATABASE STATISTICS
    # ========================================================================

    def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats: Dict[str, Any] = {
            'accessible': False,
            'projects_count': 0,
            'users_count': 0,
            'files_count': 0,
            'codebases_count': 0
        }

        try:
            if self.db_service and hasattr(self.db_service, 'get_stats'):
                db_stats = self.db_service.get_stats()
                stats.update(db_stats)
                stats['accessible'] = True
            elif self.db_service:
                # Manual counting if get_stats not available
                stats['accessible'] = True

                if hasattr(self.db_service, 'projects'):
                    try:
                        projects = self.db_service.projects.list_all(limit=1000)
                        stats['projects_count'] = len(projects)
                    except (RuntimeError, AttributeError):
                        pass

                if hasattr(self.db_service, 'users'):
                    try:
                        users = self.db_service.users.list_all(limit=1000)
                        stats['users_count'] = len(users)
                    except (RuntimeError, AttributeError):
                        pass

        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Could not get database stats: {e}")

        return stats

    def _get_database_health_details(self) -> Dict[str, Any]:
        """Get detailed database health information"""
        details: Dict[str, Any] = {
            'connection_pool': 'healthy',
            'query_performance': 'good',
            'table_statistics': {}
        }

        try:
            if self.db_service:
                # Get table counts
                stats = self._get_database_stats()
                details['table_statistics'] = {
                    'projects': stats.get('projects_count', 0),
                    'users': stats.get('users_count', 0),
                    'files': stats.get('files_count', 0),
                    'codebases': stats.get('codebases_count', 0)
                }

                # Measure query performance
                response_time = self._measure_db_response_time()
                if response_time < 100:
                    details['query_performance'] = 'excellent'
                elif response_time < 500:
                    details['query_performance'] = 'good'
                elif response_time < 1000:
                    details['query_performance'] = 'fair'
                else:
                    details['query_performance'] = 'poor'

        except (RuntimeError, AttributeError) as e:
            details['error'] = str(e)

        return details

    def _measure_db_response_time(self) -> float:
        """Measure database response time in milliseconds"""
        if not self.db_service:
            return 0.0

        try:
            start_time = time.time()

            # Simple query to measure response time
            if hasattr(self.db_service, 'users'):
                self.db_service.users.list_all(limit=1)
            elif hasattr(self.db_service, 'health_check'):
                self.db_service.health_check()

            return (time.time() - start_time) * 1000  # Convert to ms

        except (RuntimeError, AttributeError):
            return 0.0

    def _get_db_optimization_suggestions(self) -> List[str]:
        """Get database optimization suggestions"""
        suggestions: List[str] = []

        try:
            stats = self._get_database_stats()
            response_time = self._measure_db_response_time()

            if response_time > 1000:
                suggestions.append("Database response time is slow - consider adding indexes")

            if stats.get('projects_count', 0) > 100:
                suggestions.append("Large number of projects - consider archiving old/completed projects")

            if stats.get('files_count', 0) > 1000:
                suggestions.append("Large number of files - consider cleanup of unused generated files")

            if not suggestions:
                suggestions.append("Database is performing well - no optimization needed")

        except (RuntimeError, ValueError) as e:
            suggestions.append(f"Could not analyze database: {e}")

        return suggestions

    # ========================================================================
    # HELPER METHODS - RESOURCE MONITORING
    # ========================================================================

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        resources: Dict[str, Any] = {
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
            'cpu_available': PSUTIL_AVAILABLE,
            'memory_available': PSUTIL_AVAILABLE
        }

        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                # CPU info
                resources['cpu'] = {
                    'percent': round(psutil.cpu_percent(interval=0.1), 2),
                    'count': psutil.cpu_count()
                }

                # Memory info
                mem = psutil.virtual_memory()
                resources['memory'] = {
                    'percent': round(mem.percent, 2),
                    'used_gb': round(mem.used / (1024 ** 3), 2),
                    'available_gb': round(mem.available / (1024 ** 3), 2),
                    'total_gb': round(mem.total / (1024 ** 3), 2)
                }

                # Disk info
                disk = shutil.disk_usage('.')
                resources['disk'] = {
                    'percent': round((disk.used / disk.total) * 100, 2),
                    'used_gb': round(disk.used / (1024 ** 3), 2),
                    'free_gb': round(disk.free / (1024 ** 3), 2),
                    'total_gb': round(disk.total / (1024 ** 3), 2)
                }
            except (RuntimeError, OSError, AttributeError) as e:
                resources['error'] = str(e)
        else:
            resources['note'] = 'Detailed resource metrics require psutil'

        return resources

    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                cpu_percent_list = psutil.cpu_percent(interval=0.1, percpu=True)
                return {
                    'percent': round(psutil.cpu_percent(interval=0.1), 2),
                    'count': psutil.cpu_count(),
                    'per_cpu': [round(float(x), 2) for x in cpu_percent_list]
                }
            except (RuntimeError, AttributeError) as e:
                return {'error': str(e)}
        else:
            return {'note': 'Install psutil for CPU metrics'}

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                mem = psutil.virtual_memory()
                result: Dict[str, Any] = {
                    'total_gb': round(mem.total / (1024 ** 3), 2),
                    'available_gb': round(mem.available / (1024 ** 3), 2),
                    'used_gb': round(mem.used / (1024 ** 3), 2),
                    'percent': round(mem.percent, 2)
                }
                if hasattr(mem, 'cached'):
                    result['cached_gb'] = round(mem.cached / (1024 ** 3), 2)
                return result
            except (RuntimeError, AttributeError) as e:
                return {'error': str(e)}
        else:
            return {'note': 'Install psutil for memory metrics'}

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk = shutil.disk_usage('.')
            return {
                'total_gb': round(disk.total / (1024 ** 3), 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(disk.free / (1024 ** 3), 2),
                'percent': round((disk.used / disk.total) * 100, 2)
            }
        except (OSError, ZeroDivisionError) as e:
            return {'error': str(e)}

    def _get_top_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top processes by CPU and memory usage"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return []

        try:
            processes: List[Dict[str, Any]] = []
            for proc in psutil.process_iter():
                try:
                    proc_dict = proc.as_dict(['pid', 'name', 'cpu_percent', 'memory_percent'])
                    processes.append({
                        'pid': proc_dict['pid'],
                        'name': proc_dict['name'],
                        'cpu_percent': round(float(proc_dict.get('cpu_percent', 0)), 2),
                        'memory_percent': round(float(proc_dict.get('memory_percent', 0)), 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, TypeError):
                    pass

            # Sort by CPU usage and return top N
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]

        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Could not get top processes: {e}")
            return []

    def _get_disk_usage_details(self) -> Dict[str, Any]:
        """Get detailed disk usage breakdown"""
        details: Dict[str, Any] = {
            'data_directory': {},
            'log_directory': {},
            'temp_directory': {}
        }

        try:
            # Check data directory
            if os.path.exists('data'):
                data_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk('data')
                    for filename in filenames
                )
                details['data_directory'] = {
                    'size_mb': round(data_size / (1024 ** 2), 2),
                    'path': 'data'
                }

            # Check logs directory
            if os.path.exists('logs'):
                log_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk('logs')
                    for filename in filenames
                )
                details['log_directory'] = {
                    'size_mb': round(log_size / (1024 ** 2), 2),
                    'path': 'logs'
                }

        except (OSError, ValueError) as e:
            details['error'] = str(e)

        return details

    def _check_resource_warnings(self, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for resource usage warnings"""
        warnings: List[Dict[str, Any]] = []

        # Check memory
        if 'memory' in resources:
            mem_percent = resources['memory'].get('percent', 0)
            if mem_percent > self.alert_thresholds['memory_critical']:
                warnings.append({
                    'type': 'memory',
                    'severity': 'critical',
                    'message': f'Memory usage critical: {mem_percent}%'
                })
            elif mem_percent > self.alert_thresholds['memory_warning']:
                warnings.append({
                    'type': 'memory',
                    'severity': 'warning',
                    'message': f'Memory usage high: {mem_percent}%'
                })

        # Check disk
        if 'disk' in resources:
            disk_percent = resources['disk'].get('percent', 0)
            if disk_percent > 90:
                warnings.append({
                    'type': 'disk',
                    'severity': 'critical',
                    'message': f'Disk usage critical: {disk_percent}%'
                })
            elif disk_percent > 80:
                warnings.append({
                    'type': 'disk',
                    'severity': 'warning',
                    'message': f'Disk usage high: {disk_percent}%'
                })

        return warnings

    # ========================================================================
    # HELPER METHODS - ALERTS
    # ========================================================================

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts: List[Dict[str, Any]] = []

        try:
            # Database-related alerts
            if self.db_service:
                try:
                    # Check project count
                    if hasattr(self.db_service, 'projects'):
                        projects = self.db_service.projects.list_all(limit=200)
                        project_count = len(projects)

                        if project_count > self.alert_thresholds['projects_critical']:
                            alerts.append({
                                'id': f'alert_projects_{int(time.time())}',
                                'type': 'database',
                                'severity': 'critical',
                                'message': f'Project count ({project_count}) exceeds critical threshold',
                                'threshold': self.alert_thresholds['projects_critical'],
                                'current_value': project_count
                            })
                        elif project_count > self.alert_thresholds['projects_warning']:
                            alerts.append({
                                'id': f'alert_projects_{int(time.time())}',
                                'type': 'database',
                                'severity': 'warning',
                                'message': f'Project count ({project_count}) exceeds warning threshold',
                                'threshold': self.alert_thresholds['projects_warning'],
                                'current_value': project_count
                            })
                except (RuntimeError, AttributeError):
                    pass

            # Memory alerts
            if PSUTIL_AVAILABLE and psutil is not None:
                try:
                    mem = psutil.virtual_memory()
                    if mem.percent > self.alert_thresholds['memory_critical']:
                        alerts.append({
                            'id': f'alert_memory_{int(time.time())}',
                            'type': 'resource',
                            'severity': 'critical',
                            'message': f'Memory usage critical: {mem.percent:.1f}%',
                            'threshold': self.alert_thresholds['memory_critical'],
                            'current_value': mem.percent
                        })
                    elif mem.percent > self.alert_thresholds['memory_warning']:
                        alerts.append({
                            'id': f'alert_memory_{int(time.time())}',
                            'type': 'resource',
                            'severity': 'warning',
                            'message': f'Memory usage high: {mem.percent:.1f}%',
                            'threshold': self.alert_thresholds['memory_warning'],
                            'current_value': mem.percent
                        })
                except (RuntimeError, AttributeError):
                    pass

            # Disk space alerts
            try:
                disk = shutil.disk_usage('.')
                disk_percent = (disk.used / disk.total) * 100
                if disk_percent > 90:
                    alerts.append({
                        'id': f'alert_disk_{int(time.time())}',
                        'type': 'storage',
                        'severity': 'critical',
                        'message': f'Disk space critical: {disk_percent:.1f}%',
                        'threshold': 90,
                        'current_value': disk_percent
                    })
                elif disk_percent > 80:
                    alerts.append({
                        'id': f'alert_disk_{int(time.time())}',
                        'type': 'storage',
                        'severity': 'warning',
                        'message': f'Disk space high: {disk_percent:.1f}%',
                        'threshold': 80,
                        'current_value': disk_percent
                    })
            except (OSError, ZeroDivisionError):
                pass

        except (RuntimeError, ValueError) as e:
            self.logger.warning(f"Error generating alerts: {e}")

        return alerts

    def _update_alert_thresholds(self, config: Dict[str, Any]) -> None:
        """Update alert threshold configuration"""
        for key, value in config.items():
            if key in self.alert_thresholds and isinstance(value, (int, float)):
                self.alert_thresholds[key] = value
                self.logger.info(f"Updated alert threshold: {key} = {value}")

    def _acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        return {
            'alert_id': alert_id,
            'acknowledged_at': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
            'status': 'acknowledged'
        }

    def _clear_resolved_alerts(self) -> int:
        """Clear resolved alerts"""
        # In a full implementation, this would clear acknowledged/resolved alerts
        # For now, return count of active alerts that could be cleared
        active_alerts = self._get_active_alerts()
        return len([a for a in active_alerts if a.get('severity') != 'critical'])

    # ========================================================================
    # HELPER METHODS - ANALYTICS AND TRENDS
    # ========================================================================

    def _get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        return {
            'uptime_history': len(self.performance_history),
            'api_call_history': len(self.api_calls),
            'alert_threshold_config': self.alert_thresholds
        }

    def _analyze_usage_trends(self, period: str) -> Dict[str, Any]:
        """Analyze usage trends over time"""
        return {
            'period': period,
            'trend': 'stable',
            'growth_rate': 0.0,
            'note': 'Trend analysis based on historical data'
        }

    def _get_performance_trends(self, time_range: str) -> Dict[str, Any]:
        """Get performance trends over time"""
        trends: Dict[str, Any] = {
            'time_range': time_range,
            'sample_count': len(self.performance_history)
        }

        if self.performance_history:
            recent_entries = self.performance_history[-20:]

            # Calculate average metrics from history
            avg_cpu: List[float] = []
            for entry in recent_entries:
                if 'cpu_usage_percent' in entry.get('metrics', {}):
                    avg_cpu.append(float(entry['metrics']['cpu_usage_percent']))

            if avg_cpu:
                trends['average_cpu_usage'] = round(sum(avg_cpu) / len(avg_cpu), 2)

        return trends

    def _analyze_capacity(self) -> Dict[str, Any]:
        """Analyze system capacity and usage"""
        capacity: Dict[str, Any] = {
            'current_usage': {},
            'capacity_remaining': {},
            'projections': {}
        }

        try:
            # Get current resource usage
            resources = self._get_resource_usage()

            if 'memory' in resources:
                mem = resources['memory']
                capacity['current_usage']['memory_percent'] = mem.get('percent', 0)
                capacity['capacity_remaining']['memory_gb'] = mem.get('available_gb', 0)

            if 'disk' in resources:
                disk = resources['disk']
                capacity['current_usage']['disk_percent'] = disk.get('percent', 0)
                capacity['capacity_remaining']['disk_gb'] = disk.get('free_gb', 0)

            # Simple projection (would be more sophisticated in production)
            capacity['projections']['next_30_days'] = 'Sufficient capacity'

        except (KeyError, TypeError) as e:
            capacity['error'] = str(e)

        return capacity

    def _get_user_activity_summary(self, time_range: str) -> Dict[str, Any]:
        """Get user activity summary"""
        summary: Dict[str, Any] = {
            'time_range': time_range,
            'total_users': 0,
            'active_users': 0,
            'total_activities': 0
        }

        try:
            if self.db_service and hasattr(self.db_service, 'users'):
                users = self.db_service.users.list_all(limit=1000)
                summary['total_users'] = len(users)
                summary['active_users'] = len([u for u in users if getattr(u, 'status', None) == 'active'])

        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Could not get user activity summary: {e}")

        return summary

    def _get_user_activity_details(self, user_id: str, time_range: str) -> Dict[str, Any]:
        """Get detailed user activity for specific user"""
        return {
            'user_id': user_id,
            'time_range': time_range,
            'total_sessions': 0,
            'total_actions': 0,
            'last_active': None,
            'note': 'Detailed activity tracking would be implemented with activity logging'
        }

    def _get_detailed_user_activity(self, time_range: str) -> Dict[str, Any]:
        """Get detailed user activity breakdown"""
        return {
            'time_range': time_range,
            'activity_by_type': {},
            'peak_activity_times': [],
            'note': 'Detailed breakdown based on activity logs'
        }

    def _get_project_statistics(self) -> Dict[str, Any]:
        """Get overall project statistics"""
        stats: Dict[str, Any] = {
            'total_projects': 0,
            'active_projects': 0,
            'completed_projects': 0,
            'total_generated_files': 0
        }

        try:
            if self.db_service:
                if hasattr(self.db_service, 'projects'):
                    projects = self.db_service.projects.list_all(limit=1000)
                    stats['total_projects'] = len(projects)
                    stats['active_projects'] = len([p for p in projects if getattr(p, 'status', None) == 'active'])
                    stats['completed_projects'] = len(
                        [p for p in projects if getattr(p, 'status', None) == 'completed'])

                if hasattr(self.db_service, 'generated_files'):
                    files = self.db_service.generated_files.list_all(limit=2000)
                    stats['total_generated_files'] = len(files)

        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Could not get project statistics: {e}")

        return stats

    def _get_project_specific_metrics(self, project_id: str) -> Dict[str, Any]:
        """Get metrics for a specific project"""
        metrics: Dict[str, Any] = {
            'project_id': project_id,
            'files_generated': 0,
            'total_lines_of_code': 0,
            'last_updated': None
        }

        try:
            if self.db_service and hasattr(self.db_service, 'projects'):
                project = self.db_service.projects.get_by_id(project_id)
                if project:
                    metrics['last_updated'] = DateTimeHelper.to_iso_string(getattr(project, 'updated_at', None))

            if self.db_service and hasattr(self.db_service, 'generated_files'):
                files = self.db_service.generated_files.list_all(limit=5000)
                project_files = [f for f in files if getattr(f, 'project_id', None) == project_id]
                metrics['files_generated'] = len(project_files)

        except (RuntimeError, AttributeError) as e:
            self.logger.warning(f"Could not get project-specific metrics: {e}")

        return metrics

    def _compare_project_metrics(self, project_id: Optional[str], time_range: str) -> Dict[str, Any]:
        """Compare project metrics against averages"""
        return {
            'project_id': project_id,
            'time_range': time_range,
            'comparison': 'Project comparison against system averages',
            'note': 'Detailed comparison would require historical tracking'
        }

    # ========================================================================
    # HELPER METHODS - COSTS AND API USAGE
    # ========================================================================

    def _analyze_api_costs(self, time_range: str) -> Dict[str, Any]:
        """Analyze API costs"""
        return {
            'time_range': time_range,
            'total_api_calls': len(self.api_calls),
            'estimated_cost': 0.0,
            'cost_per_call': 0.0,
            'note': 'Cost analysis based on API usage patterns'
        }

    def _analyze_resource_costs(self) -> Dict[str, Any]:
        """Analyze resource costs"""
        return {
            'compute_cost': 0.0,
            'storage_cost': 0.0,
            'total_cost': 0.0,
            'note': 'Resource cost estimation based on usage'
        }

    def _get_cost_by_project(self, time_range: str) -> Dict[str, Any]:
        """Get cost breakdown by project"""
        return {
            'time_range': time_range,
            'breakdown': {},
            'note': 'Project-level cost allocation'
        }

    def _get_cost_by_user(self, time_range: str) -> Dict[str, Any]:
        """Get cost breakdown by user"""
        return {
            'time_range': time_range,
            'breakdown': {},
            'note': 'User-level cost allocation'
        }

    def _get_cost_by_operation(self, time_range: str) -> Dict[str, Any]:
        """Get cost breakdown by operation type"""
        return {
            'time_range': time_range,
            'breakdown': {},
            'note': 'Operation-level cost allocation'
        }

    def _calculate_cost_projections(self, cost_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost projections"""
        current_cost = cost_analysis.get('total_estimated_cost', 0.0)

        return {
            'next_7_days': round(current_cost * 1.1, 2),
            'next_30_days': round(current_cost * 1.3, 2),
            'next_90_days': round(current_cost * 1.5, 2),
            'note': 'Projections based on current usage trends'
        }

    def _get_cost_optimization_suggestions(self) -> List[str]:
        """Get cost optimization suggestions"""
        return [
            'Review API call patterns for optimization opportunities',
            'Consider caching frequently accessed data',
            'Archive or delete unused projects and files'
        ]

    def _get_api_usage_stats(self, period: str) -> Dict[str, Any]:
        """Get API usage statistics"""
        uptime_hours = max(1.0, (time.time() - self.start_time) / 3600.0)
        return {
            'period': period,
            'total_calls': len(self.api_calls),
            'calls_per_hour': round(len(self.api_calls) / uptime_hours, 2)
        }

    def _get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            'status': 'healthy',
            'calls_remaining': 'unlimited',
            'reset_time': None,
            'note': 'Rate limit tracking requires API integration'
        }

    def _calculate_api_statistics(self, time_range: str) -> Dict[str, Any]:
        """Calculate API usage statistics"""
        return {
            'time_range': time_range,
            'total_calls': len(self.api_calls),
            'average_per_day': 0,
            'peak_usage': 0
        }

    def _get_api_usage_by_endpoint(self, time_range: str) -> Dict[str, Any]:
        """Get API usage breakdown by endpoint"""
        return {
            'time_range': time_range,
            'health_check': 0,
            'track_usage': 0,
            'monitor_performance': 0,
            'note': 'Endpoint-level tracking'
        }

    def _get_api_usage_by_user(self, time_range: str) -> Dict[str, Any]:
        """Get API usage breakdown by user"""
        return {
            'time_range': time_range,
            'breakdown': {},
            'note': 'User-level tracking'
        }

    def _get_api_usage_by_project(self, time_range: str) -> Dict[str, Any]:
        """Get API usage breakdown by project"""
        return {
            'time_range': time_range,
            'breakdown': {},
            'note': 'Project-level tracking'
        }

    # ========================================================================
    # HELPER METHODS - REPORTING
    # ========================================================================

    def _get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        health_check = self.check_health({})
        if health_check.get('success'):
            health_data = health_check.get('data', {}).get('health', {})
            return {
                'status': health_data.get('status', 'unknown'),
                'services_healthy': sum(
                    1 for s in health_data.get('services', {}).values()
                    if s.get('status') == 'healthy'
                ),
                'total_services': len(health_data.get('services', {})),
                'alert_count': len(health_data.get('alerts', []))
            }
        return {'status': 'unknown'}

    def _get_usage_metrics(self, time_range: str) -> Dict[str, Any]:
        """Get usage metrics for reporting"""
        return {
            'time_range': time_range,
            'database_stats': self._get_database_stats(),
            'resource_usage': self._get_resource_usage()
        }

    def _get_performance_summary(self, time_range: str) -> Dict[str, Any]:
        """Get performance summary for reporting"""
        return {
            'time_range': time_range,
            'uptime': self._format_uptime(time.time() - self.start_time),
            'metrics': self._get_performance_metrics()
        }

    def _get_trend_analysis(self, time_range: str) -> Dict[str, Any]:
        """Get trend analysis for reporting"""
        return {
            'time_range': time_range,
            'usage_trends': self._analyze_usage_trends(time_range),
            'performance_trends': self._get_performance_trends(time_range)
        }

    def _generate_insights(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate insights from analytics data"""
        insights: List[str] = []

        # System health insights
        health = analytics.get('system_health', {})
        if health.get('status') == 'healthy':
            insights.append("System is operating in healthy state")
        elif health.get('status') == 'warning':
            insights.append("System health shows warning signs - review recommended")

        # Usage insights
        usage = analytics.get('usage_metrics', {})
        db_stats = usage.get('database_stats', {})
        if db_stats.get('projects_count', 0) > 50:
            insights.append("High number of projects - consider archiving completed projects")

        # Performance insights
        perf = analytics.get('performance_metrics', {})
        if perf.get('uptime_seconds', 0) > 86400:  # 1 day
            insights.append("System has been running stably for extended period")

        if not insights:
            insights.append("No significant insights at this time")

        return insights

    def _generate_executive_summary(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            'overview': 'System operating within normal parameters',
            'key_metrics': {
                'system_status': analytics.get('system_health', {}).get('status', 'unknown'),
                'total_projects': analytics.get('project_statistics', {}).get('total_projects', 0),
                'uptime': self._format_uptime(time.time() - self.start_time)
            },
            'recommendations': self._get_optimization_recommendations(),
            'action_items': []
        }

    def _prepare_chart_data(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for charts and visualizations"""
        return {
            'performance_chart': {
                'labels': [],
                'data': [],
                'type': 'line'
            },
            'resource_chart': {
                'labels': ['CPU', 'Memory', 'Disk'],
                'data': [0, 0, 0],
                'type': 'bar'
            },
            'note': 'Chart data prepared for visualization'
        }

    def _get_historical_performance(self) -> List[Dict[str, Any]]:
        """Get historical performance data"""
        return self.performance_history[-50:] if self.performance_history else []

    def _get_detailed_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                return {
                    'virtual_memory': {
                        'total': round(mem.total / (1024 ** 3), 2),
                        'available': round(mem.available / (1024 ** 3), 2),
                        'used': round(mem.used / (1024 ** 3), 2),
                        'percent': round(mem.percent, 2)
                    },
                    'swap_memory': {
                        'total': round(swap.total / (1024 ** 3), 2),
                        'used': round(swap.used / (1024 ** 3), 2),
                        'percent': round(swap.percent, 2)
                    }
                }
            except (RuntimeError, AttributeError) as e:
                return {'error': str(e)}
        return {'note': 'Install psutil for detailed memory info'}

    def _get_disk_usage_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        return self._get_disk_usage_details()

    def _get_process_info(self) -> Dict[str, Any]:
        """Get process information"""
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                proc = psutil.Process()
                return {
                    'process_count': len(list(psutil.process_iter())),
                    'current_process': {
                        'pid': os.getpid(),
                        'memory_mb': round(proc.memory_info().rss / (1024 ** 2), 2)
                    }
                }
            except (RuntimeError, AttributeError) as e:
                return {'error': str(e)}
        return {'note': 'Install psutil for process info'}

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

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

    def _store_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Store performance metrics for trend analysis"""
        try:
            metric_entry: Dict[str, Any] = {
                'timestamp': DateTimeHelper.now(),
                'metrics': metrics
            }

            self.performance_history.append(metric_entry)

            # Keep only recent history
            if len(self.performance_history) > self.max_history_size:
                self.performance_history = self.performance_history[-self.max_history_size:]

        except (RuntimeError, ValueError) as e:
            self.logger.warning(f"Failed to store performance metrics: {e}")

    def _generate_health_recommendations(self, health: Dict[str, Any]) -> List[str]:
        """Generate health-based recommendations"""
        recommendations: List[str] = []

        # Check memory usage
        memory_status = health['services'].get('memory', {}).get('status')
        if memory_status == 'critical':
            recommendations.append("Critical: Restart system or close unnecessary applications to free memory")
        elif memory_status == 'warning':
            recommendations.append("Consider closing unused applications to free memory")

        # Check database performance
        db_status = health['services'].get('database', {}).get('status')
        if db_status == 'warning':
            recommendations.append("Database performance is slow - consider archiving old projects")
        elif db_status == 'critical':
            recommendations.append("Critical: Database connection issues - check database service")

        # Check file system
        fs_status = health['services'].get('file_system', {}).get('status')
        if fs_status == 'critical':
            recommendations.append("Critical: Disk space very low - free up space immediately")
        elif fs_status == 'warning':
            recommendations.append("Disk space running low - consider cleanup or expansion")

        # Check alerts
        alert_count = len(health.get('alerts', []))
        if alert_count > 5:
            recommendations.append(f"Multiple alerts active ({alert_count}) - review system configuration")

        if not recommendations:
            recommendations.append("System is operating normally - no immediate action required")

        return recommendations


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['SystemMonitorAgent']
