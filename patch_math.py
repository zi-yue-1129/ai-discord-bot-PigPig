import re

with open('cogs/math.py', 'r', encoding='utf-8') as f:
    content = f.read()

search_code = """            # Use extracted expression
            expression = extracted

            # Safely parse expression
            sympy_expr = parse_expr(
                expression,
                transformations=transformations,
                evaluate=True,
                local_dict=local_dict,
                global_dict={'__builtins__': {}},  # Disable global_dict for safety
            )

            # Define helper functions to process Python tuples/lists recursively
            def check_has(expr: Any, *args: Any) -> bool:
                \"\"\"Recursively check if a SymPy expression or container of expressions contains targets.\"\"\"
                if isinstance(expr, (list, tuple, set)):
                    return any(check_has(item, *args) for item in expr)
                if hasattr(expr, 'has'):
                    return bool(expr.has(*args))
                return False

            def eval_numerical(expr: Any, prec: int) -> Any:
                \"\"\"Recursively evaluate a SymPy expression or container of expressions numerically.\"\"\"
                if isinstance(expr, (list, tuple, set)):
                    return type(expr)(eval_numerical(item, prec) for item in expr)
                return sympy.N(expr, prec)

            # Check for undefined functions
            from sympy.core.function import UndefinedFunction
            if check_has(sympy_expr, UndefinedFunction):
                error_message = self.lang_manager.translate(
                    guild_id, "commands", "math", "responses", "error_undefined_function"
                ) if self.lang_manager else "Error: Expression contains undefined functions."
                return error_message

            # Check for unsupported elements
            unsafe_types = (sympy.Symbol, sympy.Function)
            if check_has(sympy_expr, *unsafe_types):
                error_message = self.lang_manager.translate(
                    guild_id, "commands", "math", "responses", "error_unsupported_elements"
                ) if self.lang_manager else "Error: Expression contains unsupported elements."
                return error_message

            # Calculate result with 15 digits of precision
            result = eval_numerical(sympy_expr, 15)

            # Format result string
            result_str = str(result)
            if '.' in result_str:
                result_str = result_str.rstrip('0').rstrip('.')

            log.info(f'Calculation completed: {expression} = {result_str}')

            result_message = self.lang_manager.translate(
                guild_id, "commands", "math", "responses", "result",
                expression=expression, result=result_str
            ) if self.lang_manager else f'Result: {expression} = {result_str}'

            return result_message
        except Exception as e:"""

replace_code = """            # Use extracted expression
            expression = extracted

            # Security heuristic: prevent explosive exponentiation DoS
            if expression.count('**') > 2:
                error_message = self.lang_manager.translate(
                    guild_id, "commands", "math", "responses", "error_too_complex"
                ) if self.lang_manager else "Error: Expression is too complex."
                return error_message

            def _sync_calculate(expr_str):
                # Safely parse expression
                sympy_expr = parse_expr(
                    expr_str,
                    transformations=transformations,
                    evaluate=True,
                    local_dict=local_dict,
                    global_dict={'__builtins__': {}},  # Disable global_dict for safety
                )

                # Define helper functions to process Python tuples/lists recursively
                def check_has(expr: Any, *args: Any) -> bool:
                    \"\"\"Recursively check if a SymPy expression or container of expressions contains targets.\"\"\"
                    if isinstance(expr, (list, tuple, set)):
                        return any(check_has(item, *args) for item in expr)
                    if hasattr(expr, 'has'):
                        return bool(expr.has(*args))
                    return False

                def eval_numerical(expr: Any, prec: int) -> Any:
                    \"\"\"Recursively evaluate a SymPy expression or container of expressions numerically.\"\"\"
                    if isinstance(expr, (list, tuple, set)):
                        return type(expr)(eval_numerical(item, prec) for item in expr)
                    return sympy.N(expr, prec)

                # Check for undefined functions
                from sympy.core.function import UndefinedFunction
                if check_has(sympy_expr, UndefinedFunction):
                    return None, "error_undefined_function"

                # Check for unsupported elements
                unsafe_types = (sympy.Symbol, sympy.Function)
                if check_has(sympy_expr, *unsafe_types):
                    return None, "error_unsupported_elements"

                # Calculate result with 15 digits of precision
                result = eval_numerical(sympy_expr, 15)

                # Format result string
                result_str = str(result)
                if '.' in result_str:
                    result_str = result_str.rstrip('0').rstrip('.')

                return result_str, None

            loop = asyncio.get_running_loop()
            result_str, error_key = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_calculate, expression),
                timeout=2.0
            )

            if error_key:
                if error_key == "error_undefined_function":
                    error_message = self.lang_manager.translate(
                        guild_id, "commands", "math", "responses", "error_undefined_function"
                    ) if self.lang_manager else "Error: Expression contains undefined functions."
                    return error_message
                elif error_key == "error_unsupported_elements":
                    error_message = self.lang_manager.translate(
                        guild_id, "commands", "math", "responses", "error_unsupported_elements"
                    ) if self.lang_manager else "Error: Expression contains unsupported elements."
                    return error_message

            log.info(f'Calculation completed: {expression} = {result_str}')

            result_message = self.lang_manager.translate(
                guild_id, "commands", "math", "responses", "result",
                expression=expression, result=result_str
            ) if self.lang_manager else f'Result: {expression} = {result_str}'

            return result_message
        except asyncio.TimeoutError:
            log.warning(f"Calculation timeout for expression: {expression}")
            error_message = self.lang_manager.translate(
                guild_id, "commands", "math", "responses", "error_timeout"
            ) if self.lang_manager else "Error: Calculation timed out."
            return error_message
        except Exception as e:"""

if search_code in content:
    content = content.replace(search_code, replace_code)
    with open('cogs/math.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched cogs/math.py")
else:
    print("Could not find the search string in cogs/math.py. Writing search_code to /tmp/search_code and content to /tmp/content for debugging.")
    with open('/tmp/search_code', 'w', encoding='utf-8') as f:
        f.write(search_code)
    with open('/tmp/content', 'w', encoding='utf-8') as f:
        f.write(content)
