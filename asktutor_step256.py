from pathlib import Path
import re
import shutil
import sys

p = Path('app/agents/calculator_tool.py')
if not p.is_file():
    sys.exit('STOP: Run this script from your AskTutor project folder.')
s = p.read_text(encoding='utf-8')
if 'def _evaluate_log_sum(' in s:
    sys.exit('STOP: Step 256 already appears installed; no changes made.')
checks = ['    return _evaluate_generic(expr_text)', 'def _solve_equation(expr_text: str) -> CalculationResult:', '        steps = _linear_equation_steps(lhs, rhs, var, varname, lhs_text, rhs_text, solutions)']
if any(s.count(x) != 1 for x in checks):
    sys.exit('STOP: Unexpected calculator structure; no changes made.')
insert = '''    log_steps = _evaluate_log_sum(expr_text)
    if log_steps is not None:
        return log_steps

    index_steps = _evaluate_product_of_powers(expr_text)
    if index_steps is not None:
        return index_steps

'''
s = s.replace('    return _evaluate_generic(expr_text)', insert + '    return _evaluate_generic(expr_text)', 1)
helpers = '''# ---------- Verified teaching explanations for SS3 topics ----------

def _evaluate_log_sum(expr_text: str):
    # Strictly scoped to log(a) + log(b) with positive integer arguments.
    m = re.fullmatch(r"\\s*log\\s*\\(\\s*(\\d+)\\s*\\)\\s*\\+\\s*log\\s*\\(\\s*(\\d+)\\s*\\)\\s*", expr_text, re.I)
    if not m:
        return None
    a, b = map(int, m.groups())
    if a <= 0 or b <= 0:
        return CalculationResult(is_computable=False)
    product = a * b
    exact = sympy.simplify(sympy_log(product, 10))
    display = str(exact) if exact.is_Integer else str(sympy.N(exact, 6))
    steps = [
        f"log({a}) + log({b})",
        "Apply the product law: log(a) + log(b) = log(a × b) (base 10).",
        f"= log({a} × {b})",
        f"= log({product})",
        f"= {display}",
    ]
    return CalculationResult(True, 'evaluate', expr_text, display, steps)


def _evaluate_product_of_powers(expr_text: str):
    m = re.fullmatch(r"\\s*(-?\\d+)\\s*\\*\\*\\s*(\\d+)\\s*\\*\\s*(-?\\d+)\\s*\\*\\*\\s*(\\d+)\\s*", expr_text)
    if not m:
        return None
    a, m_exp, b, n_exp = map(int, m.groups())
    if a != b:
        return None
    if max(m_exp, n_exp) > 100:
        return None
    total = m_exp + n_exp
    result = a ** total
    steps = [
        f"{a}^{m_exp} × {a}^{n_exp}",
        "Apply the index law: a^m × a^n = a^(m+n) for the same base.",
        f"= {a}^({m_exp} + {n_exp})",
        f"= {a}^{total}",
        f"= {result}",
    ]
    return CalculationResult(True, 'evaluate', expr_text, str(result), steps)


def _exponential_equation_steps(lhs, rhs, var, varname, lhs_text, rhs_text, solutions):
    # Only a^x = b, with positive integer a != 1 and b > 0.
    if lhs.is_Pow and lhs.exp == var and lhs.base.is_Integer and rhs.is_Integer:
        base, target = int(lhs.base), int(rhs)
        if base > 0 and base != 1 and target > 0 and len(solutions) == 1:
            sol = solutions[0]
            if sympy.simplify(sol - sympy_log(target) / sympy_log(base)) == 0:
                approx = sympy.N(sol, 6)
                return [
                    f"{lhs_text} = {rhs_text}",
                    "Take logarithms of both sides (base 10).",
                    f"log({base}^{varname}) = log({target})",
                    f"Apply the power law: {varname} × log({base}) = log({target})",
                    f"Divide by log({base}): {varname} = log({target})/log({base})",
                    f"Approximate answer: {varname} ≈ {approx}",
                ]
    return None


'''
anchor = 'def _evaluate_generic(expr_text: str) -> CalculationResult:'
if s.count(anchor) != 1:
    sys.exit('STOP: Could not find insertion point.')
s = s.replace(anchor, helpers + anchor, 1)
old = '        steps = _linear_equation_steps(lhs, rhs, var, varname, lhs_text, rhs_text, solutions)'
new = '''        steps = _exponential_equation_steps(lhs, rhs, var, varname, lhs_text, rhs_text, solutions)
        if steps is None:
            steps = _linear_equation_steps(lhs, rhs, var, varname, lhs_text, rhs_text, solutions)'''
s = s.replace(old, new, 1)
try:
    compile(s, str(p), 'exec')
except SyntaxError as e:
    sys.exit(f'STOP: Generated code did not compile: {e}')
backup = p.with_name('calculator_tool_before_step256.py')
if backup.exists():
    sys.exit(f'STOP: Backup {backup} already exists; no changes made.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('SUCCESS: Step 256 installed. Backup:', backup)
