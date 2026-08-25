from __future__ import annotations

import argparse
import unittest

from cat_translate_cli.cli import _requires_local_model
from cat_translate_cli.translator import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_FILENAME,
    DEFAULT_N_CTX,
    DEFAULT_N_GPU_LAYERS,
    DEFAULT_REPO_ID,
)


def default_args() -> argparse.Namespace:
    return argparse.Namespace(
        model_path=None,
        repo_id=DEFAULT_REPO_ID,
        model=DEFAULT_MODEL_FILENAME,
        n_gpu_layers=DEFAULT_N_GPU_LAYERS,
        n_ctx=DEFAULT_N_CTX,
        max_tokens=DEFAULT_MAX_TOKENS,
    )


class LocalModelOptionTests(unittest.TestCase):
    def test_defaults_can_use_server(self) -> None:
        self.assertFalse(_requires_local_model(default_args()))

    def test_custom_context_forces_local_execution(self) -> None:
        args = default_args()
        args.n_ctx = DEFAULT_N_CTX * 2
        self.assertTrue(_requires_local_model(args))

    def test_model_path_forces_local_execution(self) -> None:
        args = default_args()
        args.model_path = "/tmp/model.gguf"
        self.assertTrue(_requires_local_model(args))


if __name__ == "__main__":
    unittest.main()
