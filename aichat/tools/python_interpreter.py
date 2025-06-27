"""
Python interpreter tool for executing Python code in a sandboxed environment.
"""
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Tuple, Optional

class PythonInterpreter:
    """
    A safe Python interpreter that can execute Python code in a controlled environment.
    
    This class provides a way to execute Python code snippets in a sandboxed environment
    with restricted access to system resources and modules.
    """
    
    def __init__(self, globals_dict: Optional[Dict[str, Any]] = None, 
                 locals_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize the Python interpreter with custom globals and locals.
        
        Args:
            globals_dict: Dictionary to use as globals when executing code
            locals_dict: Dictionary to use as locals when executing code
        """
        # Create a safe environment with limited builtins
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
        }
        
        # Create a safe globals dictionary
        self.globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
            'print': print,
        }
        
        # Update with provided globals
        if globals_dict:
            self.globals.update(globals_dict)
            
        # Use provided locals or a copy of globals
        self.locals = locals_dict if locals_dict is not None else self.globals.copy()
        
        # Initialize standard output/error capture
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()
    
    def execute(self, code: str) -> Tuple[bool, str]:
        """
        Execute Python code in the sandboxed environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        # Reset output buffers
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()
        
        try:
            # Execute the code with output redirection
            with redirect_stdout(self._stdout), redirect_stderr(self._stderr):
                # Compile the code first to catch syntax errors
                compiled_code = compile(code, '<string>', 'exec')
                # Execute the compiled code
                exec(compiled_code, self.globals, self.locals)
                
            # Get the output
            output = self._stdout.getvalue()
            return True, output
            
        except Exception as e:
            # Get the error message and traceback
            error_msg = f"Error: {str(e)}\n"
            error_msg += ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            return False, error_msg
    
    def evaluate(self, expression: str) -> Tuple[bool, Any]:
        """
        Evaluate a Python expression in the sandboxed environment.
        
        Args:
            expression: Python expression to evaluate
            
        Returns:
            Tuple of (success: bool, result: Any)
        """
        try:
            # Compile the expression
            compiled_expr = compile(expression, '<string>', 'eval')
            # Evaluate the expression
            result = eval(compiled_expr, self.globals, self.locals)
            return True, result
        except Exception as e:
            return False, str(e)
    
    def get_stdout(self) -> str:
        """Get the current stdout buffer content."""
        return self._stdout.getvalue()
    
    def get_stderr(self) -> str:
        """Get the current stderr buffer content."""
        return self._stderr.getvalue()
    
    def clear_buffers(self) -> None:
        """Clear the stdout and stderr buffers."""
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()


def execute_python_code(code: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Execute Python code in a safe environment with a timeout.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary with execution results
    """
    import signal
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
    
    interpreter = PythonInterpreter()
    
    def run_code():
        return interpreter.execute(code)
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_code)
            success, output = future.result(timeout=timeout)
            
            return {
                'success': success,
                'output': output,
                'stdout': interpreter.get_stdout(),
                'stderr': interpreter.get_stderr()
            }
            
    except FutureTimeoutError:
        return {
            'success': False,
            'output': f'Execution timed out after {timeout} seconds',
            'stdout': interpreter.get_stdout(),
            'stderr': interpreter.get_stderr()
        }
    except Exception as e:
        return {
            'success': False,
            'output': f'Error during execution: {str(e)}',
            'stdout': interpreter.get_stdout(),
            'stderr': interpreter.get_stderr()
        }
