"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Performance monitoring and metrics commands
"""

from typing import Any, Dict, List

from colorama import Fore, Style

from socratic_system.ui.commands.base import BaseCommand


class PerformanceStatusCommand(BaseCommand):
    """Display system performance status"""

    def __init__(self):
        super().__init__(
            name="performance status",
            description="Show system performance metrics",
            usage="performance status",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance status command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.performance:
            return self.error("Performance monitoring not available")

        try:
            stats = library_manager.performance.get_performance_stats()
            cache_stats = library_manager.performance.get_cache_stats()

            self.print_header("Performance Status Report")

            print(f"\n{Fore.CYAN}Execution Performance:{Style.RESET_ALL}")
            if stats:
                print(f"  Total Calls: {stats.get('total_calls', 0)}")
                print(f"  Avg Duration: {stats.get('avg_duration_ms', 0):.2f}ms")
                print(f"  Max Duration: {stats.get('max_duration_ms', 0):.2f}ms")
            else:
                print("  No execution data available")

            print(f"\n{Fore.CYAN}Cache Performance:{Style.RESET_ALL}")
            if cache_stats:
                print(f"  Cache Size: {cache_stats.get('cache_size', 0)}")
                print(f"  Hit Rate: {cache_stats.get('hit_rate', 'N/A')}")
                print(f"  Entries: {cache_stats.get('entries', 0)}")
            else:
                print("  No cache data available")

            return self.success(data={
                "execution_stats": stats,
                "cache_stats": cache_stats,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class PerformanceAgentsCommand(BaseCommand):
    """Show per-agent performance statistics"""

    def __init__(self):
        super().__init__(
            name="performance agents",
            description="Display performance metrics per agent",
            usage="performance agents",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance agents command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.performance:
            return self.error("Performance monitoring not available")

        try:
            stats = library_manager.performance.get_performance_stats()

            self.print_header("Per-Agent Performance Metrics")

            if not stats or not stats.get("agents"):
                self.print_info("No per-agent data available")
                return self.success(data={"agents": []})

            agents_data = []
            for agent_name, agent_stats in stats.get("agents", {}).items():
                agent_dict = {
                    "name": agent_name,
                    "calls": agent_stats.get("calls", 0),
                    "avg_duration_ms": agent_stats.get("avg_duration_ms", 0),
                }
                agents_data.append(agent_dict)

                print(f"\n{Fore.CYAN}{agent_name}{Style.RESET_ALL}")
                print(f"  Calls: {agent_dict['calls']}")
                print(f"  Avg Duration: {agent_dict['avg_duration_ms']:.2f}ms")

            return self.success(data={
                "agents": agents_data,
                "count": len(agents_data),
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class PerformanceCacheCommand(BaseCommand):
    """Display cache performance metrics"""

    def __init__(self):
        super().__init__(
            name="performance cache",
            description="Show cache hit rate and statistics",
            usage="performance cache",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance cache command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.performance:
            return self.error("Performance monitoring not available")

        try:
            cache_stats = library_manager.performance.get_cache_stats()

            self.print_header("Cache Performance Report")

            if not cache_stats:
                self.print_info("No cache statistics available")
                return self.success(data={"cache_stats": {}})

            print(f"\n{Fore.CYAN}Cache Statistics:{Style.RESET_ALL}")
            print(f"  Entries: {cache_stats.get('entries', 0)}")
            print(f"  Hit Rate: {cache_stats.get('hit_rate', 'N/A')}")

            return self.success(data={"cache_stats": cache_stats})

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class PerformanceBottlenecksCommand(BaseCommand):
    """Identify performance bottlenecks"""

    def __init__(self):
        super().__init__(
            name="performance bottlenecks",
            description="Find slow operations",
            usage="performance bottlenecks [threshold_ms]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance bottlenecks command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.performance:
            return self.error("Performance monitoring not available")

        threshold_ms = 1000
        if args:
            try:
                threshold_ms = float(args[0])
            except ValueError:
                return self.error("Threshold must be a number")

        try:
            slow_queries = library_manager.performance.get_slow_queries(threshold_ms)

            self.print_header(f"Performance Bottlenecks (>{threshold_ms}ms)")

            if not slow_queries:
                self.print_success(f"No operations exceeding {threshold_ms}ms")
                return self.success(data={
                    "bottlenecks": [],
                    "threshold_ms": threshold_ms,
                })

            bottlenecks_data = []
            for query in slow_queries:
                bott_dict = {
                    "name": query.get("name"),
                    "duration_ms": query.get("duration_ms"),
                }
                bottlenecks_data.append(bott_dict)

                print(f"\n{Fore.YELLOW}{bott_dict['name']}{Style.RESET_ALL}")
                print(f"  Duration: {bott_dict['duration_ms']:.2f}ms")

            return self.success(data={
                "bottlenecks": bottlenecks_data,
                "count": len(bottlenecks_data),
                "threshold_ms": threshold_ms,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class PerformanceResetCommand(BaseCommand):
    """Reset performance metrics"""

    def __init__(self):
        super().__init__(
            name="performance reset",
            description="Reset performance tracking data",
            usage="performance reset [profiler|cache|all]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance reset command"""
        orchestrator = context.get("orchestrator")

        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.performance:
            return self.error("Performance monitoring not available")

        target = args[0].lower() if args else "all"
        if target not in ["profiler", "cache", "all"]:
            return self.error("Target must be: profiler, cache, or all")

        try:
            reset_count = 0

            if target in ["profiler", "all"]:
                if library_manager.performance.reset_profiler():
                    reset_count += 1
                    self.print_success("Profiler reset")

            if target in ["cache", "all"]:
                if library_manager.performance.clear_cache():
                    reset_count += 1
                    self.print_success("Cache cleared")

            if reset_count == 0:
                return self.error("Failed to reset metrics")

            return self.success(data={
                "target": target,
                "reset_count": reset_count,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")
