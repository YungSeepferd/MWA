#!/usr/bin/env python3
"""
MAFA Health Monitor MCP Server
Provides health checks and system monitoring for the MAFA project.
"""

import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List
import subprocess


class MAFAMCPHealthServer:
    """MCP Server for MAFA system health monitoring."""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.config_path = os.getenv("MAFA_CONFIG_PATH", "config.json")
        self.initialized = False
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the MCP server."""
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mafa-health-monitor",
                "version": "1.0.0",
                "description": "Health monitoring for MAFA project"
            }
        }
    
    def handle_list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "health_check",
                    "description": "Perform comprehensive health check of MAFA system",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "description": "Perform detailed health check with full diagnostics",
                                "default": False
                            }
                        }
                    }
                },
                {
                    "name": "get_system_info",
                    "description": "Get system information and project status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "check_dependencies",
                    "description": "Check if all required dependencies are available",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "validate_config",
                    "description": "Validate MAFA configuration file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "config_path": {
                                "type": "string",
                                "description": "Path to configuration file",
                                "default": "config.json"
                            }
                        }
                    }
                }
            ]
        }
    
    def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        if not self.initialized:
            return self._error_response("Server not initialized")
        
        try:
            if name == "health_check":
                return self._health_check(arguments)
            elif name == "get_system_info":
                return self._get_system_info()
            elif name == "check_dependencies":
                return self._check_dependencies()
            elif name == "validate_config":
                return self._validate_config(arguments)
            else:
                return self._error_response(f"Unknown tool: {name}")
        except Exception as e:
            return self._error_response(f"Tool execution failed: {str(e)}")
    
    def _health_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        detailed = args.get("detailed", False)
        checks = []
        overall_status = "healthy"
        
        # Check project structure
        structure_ok = self._check_project_structure()
        checks.append({
            "name": "Project Structure",
            "status": "ok" if structure_ok else "error",
            "message": "Required files and directories present" if structure_ok else "Missing project files"
        })
        
        # Check dependencies
        deps_ok = self._check_dependencies_quick()
        checks.append({
            "name": "Dependencies",
            "status": "ok" if deps_ok else "warning",
            "message": "All dependencies available" if deps_ok else "Some dependencies may be missing"
        })
        
        # Check configuration
        config_ok, config_msg = self._check_config_quick()
        checks.append({
            "name": "Configuration",
            "status": "ok" if config_ok else "error",
            "message": config_msg
        })
        
        # Check database
        db_ok, db_msg = self._check_database_quick()
        checks.append({
            "name": "Database",
            "status": "ok" if db_ok else "warning",
            "message": db_msg
        })
        
        # Determine overall status
        error_count = sum(1 for check in checks if check["status"] == "error")
        warning_count = sum(1 for check in checks if check["status"] == "warning")
        
        if error_count > 0:
            overall_status = "unhealthy"
        elif warning_count > 0:
            overall_status = "degraded"
        
        result = {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "errors": error_count,
                "warnings": warning_count
            }
        }
        
        if detailed:
            result["details"] = self._get_detailed_health_info()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Health Check Result: {overall_status.upper()}\n" + json.dumps(result, indent=2)
                }
            ]
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system and project information."""
        info = {
            "project": {
                "name": "MAFA - Munich Apartment Finder Assistant",
                "version": "0.1.0",
                "root": str(self.project_root)
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable
            },
            "environment": {
                "config_path": self.config_path,
                "mafa_env": os.getenv("MAFA_ENV", "unknown")
            },
            "files": self._get_project_files_info()
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"System Information:\n{json.dumps(info, indent=2)}"
                }
            ]
        }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check all dependencies."""
        required_packages = [
            "selenium", "fastapi", "uvicorn", "loguru", 
            "apscheduler", "beautifulsoup4", "httpx"
        ]
        
        results = []
        all_available = True
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                results.append({
                    "package": package,
                    "status": "available",
                    "version": self._get_package_version(package)
                })
            except ImportError:
                results.append({
                    "package": package,
                    "status": "missing",
                    "version": None
                })
                all_available = False
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Dependency Check: {'All Available' if all_available else 'Some Missing'}\n" + 
                           json.dumps(results, indent=2)
                }
            ]
        }
    
    def _validate_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration file."""
        config_path = args.get("config_path", self.config_path)
        config_file = self.project_root / config_path
        
        try:
            if not config_file.exists():
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Configuration Error: File not found: {config_path}"
                        }
                    ]
                }
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Basic validation
            required_sections = ["personal_profile", "search_criteria", "notification"]
            missing_sections = [s for s in required_sections if s not in config]
            
            validation_result = {
                "valid": len(missing_sections) == 0,
                "file_path": str(config_path),
                "required_sections": required_sections,
                "missing_sections": missing_sections,
                "found_sections": list(config.keys())
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Configuration Validation:\n{json.dumps(validation_result, indent=2)}"
                    }
                ]
            }
            
        except json.JSONDecodeError as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Configuration Error: Invalid JSON - {str(e)}"
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Configuration Error: {str(e)}"
                    }
                ]
            }
    
    def _check_project_structure(self) -> bool:
        """Check if required project files exist."""
        required_files = [
            "pyproject.toml", "run.py", "mafa/orchestrator/__init__.py",
            "mafa/providers/base.py", "mafa/db/manager.py"
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                return False
        return True
    
    def _check_dependencies_quick(self) -> bool:
        """Quick dependency check."""
        try:
            import selenium
            import fastapi
            import loguru
            return True
        except ImportError:
            return False
    
    def _check_config_quick(self) -> tuple[bool, str]:
        """Quick configuration check."""
        config_file = self.project_root / self.config_path
        if not config_file.exists():
            return False, f"Configuration file not found: {self.config_path}"
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if "notification" in config and "discord_webhook_url" in config["notification"]:
                return True, "Configuration valid"
            else:
                return True, "Configuration found but may be incomplete"
                
        except Exception as e:
            return False, f"Configuration error: {str(e)}"
    
    def _check_database_quick(self) -> tuple[bool, str]:
        """Quick database check."""
        db_file = self.project_root / "data" / "contacts.db"
        if db_file.exists():
            return True, "Database file exists"
        else:
            return True, "No existing database (will be created on first run)"
    
    def _get_detailed_health_info(self) -> Dict[str, Any]:
        """Get detailed health information."""
        return {
            "system": {
                "platform": sys.platform,
                "python_version": sys.version.split()[0],
                "working_directory": os.getcwd()
            },
            "project_structure": self._get_project_files_info(),
            "environment_variables": {k: v for k, v in os.environ.items() if k.startswith("MAFA_")}
        }
    
    def _get_project_files_info(self) -> Dict[str, str]:
        """Get information about project files."""
        important_files = [
            "pyproject.toml", "config.json", "Dockerfile", "docker-compose.yml",
            "mafa/orchestrator/__init__.py", "mafa/providers/base.py",
            "tests/", "api/main.py"
        ]
        
        info = {}
        for file_path in important_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                info[file_path] = "exists"
            else:
                info[file_path] = "missing"
        
        return info
    
    def _get_package_version(self, package: str) -> str:
        """Get version of a package."""
        try:
            import importlib.metadata
            return importlib.metadata.version(package.replace("-", "_"))
        except:
            return "unknown"
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {message}"
                }
            ]
        }


def main():
    """Main MCP server loop."""
    server = MAFAMCPHealthServer()
    
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
                
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "initialize":
                response = server.handle_initialize(params)
            elif method == "tools/list":
                response = server.handle_list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = server.handle_call_tool(tool_name, arguments)
            else:
                response = {"error": {"code": -32601, "message": "Method not found"}}
            
            # Send response
            print(json.dumps({"id": request.get("id"), "result": response}))
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(json.dumps({"error": {"code": -32603, "message": f"Internal error: {str(e)}"}}))


if __name__ == "__main__":
    main()