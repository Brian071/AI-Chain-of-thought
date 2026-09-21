import unittest
from app.backend import ResponseProcessor
from app.model_manager import ModelManager

class TestBackend(unittest.TestCase):
    def test_cot_parsing(self):
        sample = "<think>\nStep 1: Analyze problem.\nStep 2: Calculate.\n</think>\n\nFinal result is 42."
        reasoning, answer = ResponseProcessor.parse_cot_reasoning(sample)
        self.assertIn("Step 1", reasoning)
        self.assertEqual(answer, "Final result is 42.")

    def test_latex_to_mathml(self):
        latex = "$$E = mc^2$$"
        mathml = ResponseProcessor.latex_to_mathml(latex)
        self.assertIn('<math xmlns="http://www.w3.org/1998/Math/MathML"', mathml)
        self.assertIn("E = mc^2", mathml)

    def test_model_manager_mock_load_and_stream(self):
        mm = ModelManager()
        mm.load_model("dummy.gguf", use_mock=True)
        self.assertTrue(mm.current_model is not None)

        messages = [{"role": "user", "content": "Berapa 1+1?"}]
        stream = list(mm.generate_stream(messages, reasoning_mode=True))
        full_text = "".join(stream)
        self.assertIn("<think>", full_text)
        self.assertIn("1. Langkah pertama selesai.", full_text)

if __name__ == "__main__":
    unittest.main()
