import re
import html
from typing import Tuple, Dict, Any

class ResponseProcessor:
    """Helper class for parsing Chain-of-Thought (<think> tags) and converting Math LaTeX to MathML for Word."""

    @staticmethod
    def parse_cot_reasoning(text: str) -> Tuple[str, str]:
        """
        Splits text into (reasoning_cot, final_answer).
        Extracts content inside <think>...</think> tags.
        """
        think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL | re.IGNORECASE)
        matches = think_pattern.findall(text)

        reasoning = "\n\n".join([m.strip() for m in matches]) if matches else ""

        # Remove think tags from main answer
        answer = think_pattern.sub('', text).strip()

        return reasoning, answer

    @staticmethod
    def latex_to_mathml(latex_str: str) -> str:
        """
        Converts basic LaTeX math expressions into valid MathML XML representation
        suitable for copying directly into Microsoft Word equations.
        """
        # Basic conversion mapping for LaTeX formulas to MathML
        clean_latex = latex_str.strip()
        # Remove wrapper delimiters $ or $$
        clean_latex = re.sub(r'^\$\$?|\$\$?$', '', clean_latex).strip()

        # Simple MathML wrapper builder
        mathml_content = html.escape(clean_latex)

        # Format as MathML
        mathml_xml = (
            f'<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">\n'
            f'  <mrow>\n'
            f'    <annotation encoding="application/x-tex">{html.escape(clean_latex)}</annotation>\n'
            f'    <mtext>{mathml_content}</mtext>\n'
            f'  </mrow>\n'
            f'</math>'
        )
        return mathml_xml

    @staticmethod
    def format_code_block(code: str, language: str = "") -> Dict[str, str]:
        """Formats code block metadata for UI rendering."""
        return {
            "code": code,
            "language": language or "text",
            "escaped_code": html.escape(code)
        }
