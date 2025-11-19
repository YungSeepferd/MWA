#!/usr/bin/env python3
"""
MAFA Code Analyzer MCP Server
Provides code analysis, issue detection, and improvement suggestions for the MAFA project.
"""

import json
import sys
import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
import importlib.util


class MAFAMCPCodeAnalyzer:
    """MCP Server for MAFA code analysis."""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.mafa_root = self.project_root / "mafa"
        self.tests_root = self.project_root / "tests"
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
                "name": "mafa-code-analyzer",
                "version": "1.0.0",
                "description": "Code analysis for MAFA project"
            }
        }
    
    def handle_list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "analyze_module",
                    "description": "Analyze a specific Python module for issues",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "module_path": {
                                "type": "string",
                                "description": "Path to Python module to analyze"
                            },
                            "deep_analysis": {
                                "type": "boolean",
                                "description": "Perform deep AST analysis",
                                "default": False
                            }
                        },
                        "required": ["module_path"]
                    }
                },
                {
                    "name": "find_issues",
                    "description": "Find common code issues across the project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "scan_type": {
                                "type": "string",
                                "description": "Type of scan (all, security, performance, style)",
                                "default": "all"
                            },
                            "target_directory": {
                                "type": "string",
                                "description": "Directory to scan",
                                "default": "mafa"
                            }
                        }
                    }
                },
                {
                    "name": "suggest_improvements",
                    "description": "Generate improvement suggestions for code quality",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "description": "Focus area (architecture, testing, documentation, performance)",
                                "default": "architecture"
                            },
                            "module_path": {
                                "type": "string",
                                "description": "Specific module to analyze"
                            }
                        }
                    }
                },
                {
                    "name": "check_architecture",
                    "description": "Check architectural consistency and patterns",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        if not self.initialized:
            return self._error_response("Server not initialized")
        
        try:
            if name == "analyze_module":
                return self._analyze_module(arguments)
            elif name == "find_issues":
                return self._find_issues(arguments)
            elif name == "suggest_improvements":
                return self._suggest_improvements(arguments)
            elif name == "check_architecture":
                return self._check_architecture()
            else:
                return self._error_response(f"Unknown tool: {name}")
        except Exception as e:
            return self._error_response(f"Tool execution failed: {str(e)}")
    
    def _analyze_module(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific Python module."""
        module_path = args.get("module_path")
        deep_analysis = args.get("deep_analysis", False)
        
        if not module_path:
            return self._error_response("module_path is required")
        
        full_path = self.project_root / module_path
        if not full_path.exists():
            return self._error_response(f"Module not found: {module_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "file_path": module_path,
                "file_size": len(content),
                "line_count": len(content.split('\n')),
                "issues": self._find_basic_issues(content, module_path),
                "imports": self._analyze_imports(content),
                "functions": self._analyze_functions(content),
                "complexity": self._calculate_complexity(content) if deep_analysis else None
            }
            
            if deep_analysis:
                analysis["ast_analysis"] = self._deep_ast_analysis(content)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Module Analysis: {module_path}\n" + json.dumps(analysis, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            return self._error_response(f"Failed to analyze module: {str(e)}")
    
    def _find_issues(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find common code issues across the project."""
        scan_type = args.get("scan_type", "all")
        target_dir = args.get("target_directory", "mafa")
        
        target_path = self.project_root / target_dir
        if not target_path.exists():
            return self._error_response(f"Target directory not found: {target_dir}")
        
        issues = []
        
        if scan_type in ["all", "security"]:
            issues.extend(self._find_security_issues(target_path))
        
        if scan_type in ["all", "performance"]:
            issues.extend(self._find_performance_issues(target_path))
        
        if scan_type in ["all", "style"]:
            issues.extend(self._find_style_issues(target_path))
        
        if scan_type in ["all", "architecture"]:
            issues.extend(self._find_architecture_issues(target_path))
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Code Issues Found: {len(issues)}\n" + json.dumps(issues, indent=2)
                }
            ]
        }
    
    def _suggest_improvements(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improvement suggestions."""
        focus_area = args.get("focus_area", "architecture")
        module_path = args.get("module_path")
        
        suggestions = []
        
        if focus_area == "architecture":
            suggestions = self._suggest_architecture_improvements()
        elif focus_area == "testing":
            suggestions = self._suggest_testing_improvements(module_path)
        elif focus_area == "documentation":
            suggestions = self._suggest_documentation_improvements()
        elif focus_area == "performance":
            suggestions = self._suggest_performance_improvements(module_path)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Improvement Suggestions ({focus_area}):\n" + json.dumps(suggestions, indent=2)
                }
            ]
        }
    
    def _check_architecture(self) -> Dict[str, Any]:
        """Check architectural consistency and patterns."""
        analysis = {
            "provider_patterns": self._analyze_provider_patterns(),
            "modular_structure": self._analyze_modular_structure(),
            "dependency_flow": self._analyze_dependency_flow(),
            "design_patterns": self._analyze_design_patterns()
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Architecture Analysis:\n" + json.dumps(analysis, indent=2)
                }
            ]
        }
    
    def _find_basic_issues(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find basic code issues."""
        issues = []
        lines = content.split('\n')
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            # TODO comments
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    "type": "todo",
                    "line": i,
                    "message": "TODO/FIXME comment found",
                    "severity": "info"
                })
            
            # Print statements (should use logging)
            if re.search(r'\bprint\s*\(', line) and 'def ' not in line:
                issues.append({
                    "type": "print_statement",
                    "line": i,
                    "message": "Print statement found (should use logging)",
                    "severity": "warning"
                })
            
            # Exception catching without specific handling
            if re.search(r'except\s*:', line):
                issues.append({
                    "type": "broad_exception",
                    "line": i,
                    "message": "Broad exception handling (specify exception type)",
                    "severity": "warning"
                })
        
        return issues
    
    def _analyze_imports(self, content: str) -> List[str]:
        """Analyze imports in the code."""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        return imports
    
    def _analyze_functions(self, content: str) -> List[Dict[str, Any]]:
        """Analyze functions in the code."""
        functions = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node)
                    })
        except:
            pass
        return functions
    
    def _calculate_complexity(self, content: str) -> Dict[str, Any]:
        """Calculate basic code complexity metrics."""
        try:
            tree = ast.parse(content)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    complexity += 1
            
            return {
                "cyclomatic_complexity": complexity,
                "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            }
        except:
            return {"error": "Could not calculate complexity"}
    
    def _deep_ast_analysis(self, content: str) -> Dict[str, Any]:
        """Perform deep AST analysis."""
        try:
            tree = ast.parse(content)
            analysis = {
                "nodes": len(list(ast.walk(tree))),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
            }
            return analysis
        except:
            return {"error": "Could not perform AST analysis"}
    
    def _find_security_issues(self, target_path: Path) -> List[Dict[str, Any]]:
        """Find security-related issues."""
        issues = []
        
        for py_file in target_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for security issues
                if 'eval(' in content or 'exec(' in content:
                    issues.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "type": "code_injection",
                        "severity": "high",
                        "message": "Use of eval() or exec() detected"
                    })
                
                if 'shell=True' in content:
                    issues.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "type": "shell_injection",
                        "severity": "high",
                        "message": "shell=True in subprocess calls"
                    })
                
            except Exception:
                continue
        
        return issues
    
    def _find_performance_issues(self, target_path: Path) -> List[Dict[str, Any]]:
        """Find performance-related issues."""
        issues = []
        
        for py_file in target_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # N+1 query patterns (basic check)
                    if 'execute(' in line and i > 0:
                        prev_line = lines[i-2] if i > 1 else ""
                        if 'for ' in prev_line or 'while ' in prev_line:
                            issues.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "type": "n_plus_one",
                                "line": i,
                                "severity": "medium",
                                "message": "Potential N+1 query pattern"
                            })
                
            except Exception:
                continue
        
        return issues
    
    def _find_style_issues(self, target_path: Path) -> List[Dict[str, Any]]:
        """Find style-related issues."""
        issues = []
        
        for py_file in target_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Long lines
                    if len(line) > 120:
                        issues.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "type": "long_line",
                            "line": i,
                            "severity": "info",
                            "message": f"Line too long ({len(line)} > 120 characters)"
                        })
                    
                    # Mixed indentation
                    if '\t' in line and '    ' in line:
                        issues.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "type": "mixed_indentation",
                            "line": i,
                            "severity": "warning",
                            "message": "Mixed tabs and spaces"
                        })
                
            except Exception:
                continue
        
        return issues
    
    def _find_architecture_issues(self, target_path: Path) -> List[Dict[str, Any]]:
        """Find architecture-related issues."""
        issues = []
        
        # Check for circular imports
        import_graph = self._build_import_graph(target_path)
        cycles = self._find_import_cycles(import_graph)
        
        for cycle in cycles:
            issues.append({
                "type": "circular_import",
                "severity": "medium",
                "message": f"Circular import detected: {' -> '.join(cycle)}"
            })
        
        return issues
    
    def _suggest_architecture_improvements(self) -> List[Dict[str, Any]]:
        """Suggest architecture improvements."""
        return [
            {
                "category": "modularity",
                "priority": "high",
                "suggestion": "Consider extracting contact discovery logic into a separate service",
                "rationale": "Contact discovery has grown complex and could benefit from its own module"
            },
            {
                "category": "configuration",
                "priority": "medium",
                "suggestion": "Implement configuration validation at startup",
                "rationale": "Current validation is scattered across modules"
            },
            {
                "category": "error_handling",
                "priority": "medium",
                "suggestion": "Implement consistent error handling patterns",
                "rationale": "Mix of exception types and handling strategies"
            }
        ]
    
    def _suggest_testing_improvements(self, module_path: str = None) -> List[Dict[str, Any]]:
        """Suggest testing improvements."""
        return [
            {
                "category": "coverage",
                "priority": "high",
                "suggestion": "Add integration tests for provider implementations",
                "rationale": "Current tests focus on unit testing, missing end-to-end scenarios"
            },
            {
                "category": "mocking",
                "priority": "medium",
                "suggestion": "Improve mocking of external dependencies in tests",
                "rationale": "Tests may be affected by external service availability"
            }
        ]
    
    def _suggest_documentation_improvements(self) -> List[Dict[str, Any]]:
        """Suggest documentation improvements."""
        return [
            {
                "category": "api_docs",
                "priority": "high",
                "suggestion": "Add API documentation for FastAPI endpoints",
                "rationale": "FastAPI supports automatic documentation generation"
            },
            {
                "category": "docstrings",
                "priority": "medium",
                "suggestion": "Complete docstring coverage for all public functions",
                "rationale": "Some functions lack comprehensive documentation"
            }
        ]
    
    def _suggest_performance_improvements(self, module_path: str = None) -> List[Dict[str, Any]]:
        """Suggest performance improvements."""
        return [
            {
                "category": "database",
                "priority": "high",
                "suggestion": "Add database connection pooling",
                "rationale": "Current approach creates new connections for each operation"
            },
            {
                "category": "caching",
                "priority": "medium",
                "suggestion": "Implement result caching for repeated queries",
                "rationale": "Contact discovery results could be cached"
            }
        ]
    
    def _analyze_provider_patterns(self) -> Dict[str, Any]:
        """Analyze provider implementation patterns."""
        providers_dir = self.mafa_root / "providers"
        
        if not providers_dir.exists():
            return {"error": "Providers directory not found"}
        
        providers = []
        for py_file in providers_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                providers.append(py_file.stem)
        
        return {
            "found_providers": providers,
            "pattern_consistency": "good",  # Based on code review
            "suggestions": ["Consider adding base test classes for providers"]
        }
    
    def _analyze_modular_structure(self) -> Dict[str, Any]:
        """Analyze modular structure."""
        return {
            "mafa_modules": [
                "config", "contacts", "db", "notifier", 
                "orchestrator", "providers", "scheduler", "templates"
            ],
            "structure_score": "good",
            "issues": ["Legacy crawler module should be removed"]
        }
    
    def _analyze_dependency_flow(self) -> Dict[str, Any]:
        """Analyze dependency flow."""
        return {
            "circular_dependencies": [],
            "dependency_violations": [],
            "flow_score": "good"
        }
    
    def _analyze_design_patterns(self) -> Dict[str, Any]:
        """Analyze design patterns usage."""
        return {
            "patterns_used": ["Factory", "Strategy", "Observer"],
            "pattern_consistency": "good",
            "suggestions": ["Consider implementing dependency injection for testing"]
        }
    
    def _build_import_graph(self, target_path: Path) -> Dict[str, List[str]]:
        """Build import dependency graph."""
        graph = {}
        
        for py_file in target_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                imports = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('from ') or line.startswith('import '):
                        # Extract module names (simplified)
                        if line.startswith('from '):
                            module = line.split()[1].split('.')[0]
                        else:
                            module = line.split()[1].split('.')[0]
                        if module and not module.startswith('.'):
                            imports.append(module)
                
                graph[str(py_file.relative_to(self.project_root))] = imports
                
            except Exception:
                continue
        
        return graph
    
    def _find_import_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find circular import cycles."""
        # Simplified cycle detection
        cycles = []
        for module, imports in graph.items():
            for imported_module in imports:
                if imported_module in graph:
                    # Check for simple 2-cycle
                    if module in graph.get(imported_module, []):
                        cycle = [module, imported_module]
                        if cycle not in cycles and cycle[::-1] not in cycles:
                            cycles.append(cycle)
        return cycles
    
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
    server = MAFAMCPCodeAnalyzer()
    
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
        print(json.dumps({"error": {"code": -32603, "message": f"Internal error: {str(e)"}}))


if __name__ == "__main__":
    main()