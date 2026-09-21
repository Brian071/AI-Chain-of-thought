import os
import glob
from typing import List, Dict, Any, Optional, Generator

# Try importing Llama from llama_cpp, or mock if not available (for fallback/testing)
try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False
    Llama = None


class MockLlama:
    """Mock Llama class for testing environments without compiled llama-cpp weights."""
    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        self.kwargs = kwargs

    def create_chat_completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs):
        last_msg = messages[-1]["content"] if messages else ""
        if "reasoning" in kwargs and kwargs.get("reasoning", True) or kwargs.get("temperature", 0.7) > 0.1:
            dummy_resp = (
                "<think>\nMemproses permintaan tugas pengguna.\n"
                "Menganalisis pertanyaan secara bertahap...\n</think>\n\n"
                f"Berikut hasil analisis untuk: {last_msg}\n"
                "1. Langkah pertama selesai.\n"
                "2. Persamaan matematika: $$E = mc^2$$\n"
                "```python\nprint('Hello World')\n```"
            )
        else:
            dummy_resp = f"Jawaban langsung untuk: {last_msg}"

        if stream:
            def generator():
                chunk_size = 8
                for i in range(0, len(dummy_resp), chunk_size):
                    chunk = dummy_resp[i:i+chunk_size]
                    yield {
                        "choices": [
                            {
                                "delta": {"content": chunk},
                                "finish_reason": None if i + chunk_size < len(dummy_resp) else "stop"
                            }
                        ]
                    }
            return generator()
        else:
            return {
                "choices": [
                    {
                        "message": {"content": dummy_resp},
                        "finish_reason": "stop"
                    }
                ]
            }


class ModelManager:
    def __init__(self):
        self.current_model: Optional[Any] = None
        self.current_model_path: Optional[str] = None
        self.use_mock: bool = False

    def scan_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Scans the given directory for .gguf model files."""
        if not directory_path or not os.path.exists(directory_path):
            return []

        gguf_files = []
        if os.path.isfile(directory_path) and directory_path.endswith(".gguf"):
            files = [directory_path]
        else:
            files = glob.glob(os.path.join(directory_path, "**", "*.gguf"), recursive=True)

        for file_path in files:
            file_name = os.path.basename(file_path)
            size_bytes = os.path.getsize(file_path)
            size_gb = round(size_bytes / (1024 ** 3), 2)
            gguf_files.append({
                "name": file_name,
                "path": os.path.abspath(file_path),
                "size_gb": size_gb,
                "size_formatted": f"{size_gb} GB"
            })

        return sorted(gguf_files, key=lambda x: x["name"])

    def load_model(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        n_batch: int = 512,
        n_ubatch: int = 512,
        use_mmap: bool = True,
        use_mlock: bool = False,
        use_mock: bool = False
    ) -> bool:
        """Loads a GGUF model with low VRAM / Chunked Batch settings."""
        if not use_mock and not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Unload previous model if exists
        self.unload_model()

        self.use_mock = use_mock or not HAS_LLAMA_CPP

        if self.use_mock:
            self.current_model = MockLlama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,
                n_ubatch=n_ubatch
            )
        else:
            # Load with llama_cpp
            self.current_model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,        # Chunked batch processing size
                n_ubatch=n_ubatch,      # Micro-batch size to prevent OOM
                use_mmap=use_mmap,
                use_mlock=use_mlock,
                verbose=False
            )

        self.current_model_path = model_path
        return True

    def unload_model(self):
        """Frees the current model from RAM/VRAM."""
        if self.current_model is not None:
            del self.current_model
            self.current_model = None
            self.current_model_path = None
            import gc
            gc.collect()

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        reasoning_mode: bool = True,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Streams completion tokens from loaded model."""
        if self.current_model is None:
            raise RuntimeError("No model is currently loaded.")

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        # Inject instructions for reasoning mode or normal mode if needed
        for msg in messages:
            formatted_messages.append(msg)

        if HAS_LLAMA_CPP and not self.use_mock:
            response_stream = self.current_model.create_chat_completion(
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True
            )
            for chunk in response_stream:
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
        else:
            response_stream = self.current_model.create_chat_completion(
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True,
                reasoning=reasoning_mode
            )
            for chunk in response_stream:
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
