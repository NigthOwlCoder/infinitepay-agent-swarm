import ast
import operator
import re

from model.chat_request import ChatRequest


class UtilityAgent:
    """Answer deterministic arithmetic without executing arbitrary code."""

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def handle(self, request: ChatRequest) -> dict:
        expression = self._extract_expression(request.message)
        try:
            result = self._evaluate(ast.parse(expression, mode="eval").body)
            answer = f"O resultado é {self._format(result)}."
        except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            answer = "Não consegui calcular essa expressão com segurança."

        return {
            "agent": "utility",
            "answer": answer,
            "sources": ["Cálculo determinístico local"],
            "needs_human": False,
        }

    @staticmethod
    def _extract_expression(message: str) -> str:
        normalized = message.casefold().replace("×", "*").replace("x", "*")
        normalized = normalized.replace("÷", "/").replace("^", "**")
        match = re.search(
            r"[-+]?\d+(?:[.,]\d+)?(?:\s*[-+*/%]\s*[-+]?\d+(?:[.,]\d+)?)+",
            normalized,
        )
        return match.group(0).replace(",", ".").strip() if match else ""

    def _evaluate(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self.OPERATORS:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            if abs(left) > 1_000_000 or abs(right) > 1_000_000:
                raise ValueError("operands exceed safe limit")
            return self.OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.OPERATORS:
            return self.OPERATORS[type(node.op)](self._evaluate(node.operand))
        raise TypeError("unsupported expression")

    @staticmethod
    def _format(value: int | float) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(round(value, 8)).replace(".", ",")
