"""
Python code interpreter with sandboxing for safe code execution.
"""
import io
import sys
import os
import contextlib
import traceback
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Set matplotlib to use 'Agg' backend to avoid GUI windows
matplotlib.use('Agg')

class CodeInterpreter:
    """
    A secure Python code interpreter that executes code in a restricted environment.
    """
    
    def __init__(self, timeout: int = 30, max_output_length: int = 10000):
        """
        Initialize the code interpreter.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_length: Maximum length of output (in characters) to return
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
        self.local_vars = {}
        self.reset_environment()
        
    def reset_environment(self) -> None:
        """Reset the execution environment to a clean state."""
        # Create a safe environment with only the necessary built-ins
        safe_builtins = {
            'None': None,
            'False': False,
            'True': True,
            'abs': abs,
            'all': all,
            'any': any,
            'ascii': ascii,
            'bin': bin,
            'bool': bool,
            'bytearray': bytearray,
            'bytes': bytes,
            'chr': chr,
            'complex': complex,
            'dict': dict,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'hash': hash,
            'hex': hex,
            'int': int,
            'iter': iter,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'next': next,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'range': range,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            # Math functions
            '__import__': self._safe_import,
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            're': __import__('re'),
            'collections': __import__('collections'),
            'itertools': __import__('itertools'),
            'functools': __import__('functools'),
            'os': self._create_safe_os_module(),
            'sys': self._create_safe_sys_module(),
            # Data science libraries
            'np': np,
            'pd': pd,
            'plt': plt,
            'matplotlib': matplotlib,
        }
        
        # Add numpy functions to the global namespace
        for name in dir(np):
            if not name.startswith('_'):
                safe_builtins[f'np.{name}'] = getattr(np, name)
                
        # Add pandas functions
        for name in dir(pd):
            if not name.startswith('_'):
                safe_builtins[f'pd.{name}'] = getattr(pd, name)
        
        self.local_vars = safe_builtins.copy()
        self.local_vars.update({
            '__builtins__': safe_builtins,
            '_name__': '__main__',
        })
    
    def _create_safe_os_module(self) -> object:
        """Create a safe version of the os module."""
        safe_os = {}
        for name in dir(os):
            if name in {
                'name', 'path', 'getcwd', 'listdir', 'makedirs', 'mkdir',
                'pathsep', 'sep', 'linesep', 'environ'
            }:
                safe_os[name] = getattr(os, name)
        
        # Add path module with safe functions
        safe_os['path'] = {
            'join': os.path.join,
            'exists': os.path.exists,
            'isdir': os.path.isdir,
            'isfile': os.path.isfile,
            'splitext': os.path.splitext,
            'basename': os.path.basename,
            'dirname': os.path.dirname,
            'abspath': os.path.abspath,
            'normpath': os.path.normpath,
        }
        
        return type('module', (), safe_os)
    
    def _create_safe_sys_module(self) -> object:
        """Create a safe version of the sys module."""
        return type('module', (), {
            'version': sys.version,
            'version_info': sys.version_info,
            'executable': sys.executable,
            'platform': sys.platform,
            'maxsize': sys.maxsize,
            'path': sys.path.copy(),
            'argv': [],
        })
    
    def _safe_import(self, name: str, globals=None, locals=None, fromlist=(), level=0):
        """A safe version of __import__ that restricts what can be imported."""
        ALLOWED_MODULES = {
            'math', 'random', 'datetime', 'json', 're', 'collections',
            'itertools', 'functools', 'numpy', 'pandas', 'matplotlib'
        }
        
        if name not in ALLOWED_MODULES:
            raise ImportError(f"Import of '{name}' is not allowed")
        return __import__(name, globals, locals, fromlist, level)
    
    def execute_code(
        self,
        code: str,
        local_vars: Optional[Dict] = None,
        return_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Python code in a restricted environment.
        
        Args:
            code: The Python code to execute
            local_vars: Additional local variables to include in the execution environment
            return_output: Whether to capture and return the output
            
        Returns:
            Dictionary with execution results, output, and any error information
        """
        # Prepare the execution environment
        exec_locals = self.local_vars.copy()
        if local_vars:
            exec_locals.update(local_vars)
        
        # Redirect stdout and stderr
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        # Prepare the result dictionary
        result = {
            'success': False,
            'output': '',
            'error': None,
            'exception': None,
            'traceback': None,
            'variables': {},
            'plots': [],
            'execution_time': 0.0
        }
        
        # Add print statements to the code to capture output
        if return_output:
            code = (
                "import sys\n"
                "_original_stdout = sys.stdout\n"
                "_original_stderr = sys.stderr\n"
                f"sys.stdout = sys.stderr = open({stdout!r}, 'w')\n"
                "try:\n"
                "    _output = None\n"
                "    # User code starts here\n"
            )
            
            # Indent the user code
            for line in code.splitlines():
                code += f"    {line}\n"
                
            # Add code to capture the last expression result
            code += (
                "    # User code ends here\n"
                "except Exception as e:\n"
                "    raise e\n"
                "finally:\n"
                "    sys.stdout = _original_stdout\n"
                "    sys.stderr = _original_stderr\n"
            )
        
        # Execute the code
        start_time = time.time()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                # Execute the code with a timeout
                exec(compile(code, '<string>', 'exec'), {}, exec_locals)
                
                # Get the output
                output = stdout.getvalue()
                if output:
                    result['output'] = output[:self.max_output_length]
                
                # Check for plots and save them
                if 'plt' in exec_locals and len(plt.get_fignums()) > 0:
                    os.makedirs('generated_plots', exist_ok=True)
                    for i, fig_num in enumerate(plt.get_fignums()):
                        fig = plt.figure(fig_num)
                        filename = f'generated_plots/plot_{int(time.time())}_{i}.png'
                        fig.savefig(filename)
                        plt.close(fig)
                        result['plots'].append(filename)
                
                # Get variables that were created/modified
                for var_name, var_value in exec_locals.items():
                    if not var_name.startswith('_') and var_name not in self.local_vars:
                        # Convert numpy arrays and pandas DataFrames to lists/dicts for serialization
                        if isinstance(var_value, (np.ndarray, pd.DataFrame, pd.Series)):
                            try:
                                if hasattr(var_value, 'to_dict'):
                                    result['variables'][var_name] = var_value.to_dict()
                                else:
                                    result['variables'][var_name] = var_value.tolist()
                            except:
                                result['variables'][var_name] = str(var_value)
                        elif isinstance(var_value, (int, float, str, bool, list, dict, tuple, set, type(None))):
                            result['variables'][var_name] = var_value
                        else:
                            result['variables'][var_name] = str(var_value)
                
                result['success'] = True
                
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['exception'] = type(e).__name__
            result['traceback'] = traceback.format_exc()
        finally:
            result['execution_time'] = time.time() - start_time
            
        return result

    def execute_code_block(self, code_block: str, language: str = 'python') -> Dict[str, Any]:
        """
        Execute a code block with optional language specification.
        
        Args:
            code_block: The code block to execute
            language: The programming language of the code block
            
        Returns:
            Dictionary with execution results
        """
        if language.lower() == 'python':
            return self.execute_code(code_block)
        else:
            return {
                'success': False,
                'error': f'Unsupported language: {language}',
                'output': ''
            }


# Example usage
if __name__ == "__main__":
    interpreter = CodeInterpreter()
    
    # Example 1: Simple calculation
    result = interpreter.execute_code("x = 5\ny = 10\nz = x + y\nprint(f'The sum of {x} and {y} is {z}')")
    print("Example 1:", result)
    
    # Example 2: Data analysis with pandas and matplotlib
    code = """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Create a sample DataFrame
    data = {'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
            'Age': [25, 30, 35, 40, 45],
            'Salary': [50000, 60000, 70000, 80000, 90000]}
    df = pd.DataFrame(data)
    
    # Calculate average salary
    avg_salary = df['Salary'].mean()
    
    # Create a plot
    plt.figure(figsize=(8, 4))
    plt.bar(df['Name'], df['Salary'])
    plt.axhline(y=avg_salary, color='r', linestyle='--', label=f'Average: ${avg_salary:,.2f}')
    plt.title('Employee Salaries')
    plt.xlabel('Employee')
    plt.ylabel('Salary ($)')
    plt.legend()
    plt.tight_layout()
    
    # Show some statistics
    print("Employee Data:")
    print(df)
    print(f"\nAverage Salary: ${avg_salary:,.2f}")
    """
    
    result = interpreter.execute_code(code)
    print("\nExample 2: Success:", result['success'])
    print("Output:", result['output'][:500] + '...' if len(result['output']) > 500 else result['output'])
    print("Variables:", list(result['variables'].keys()))
    if result['plots']:
        print(f"Plots saved to: {result['plots'][0]}")
