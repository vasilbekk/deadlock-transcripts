"""
CUDA runtime library configuration for faster-whisper
"""

import importlib
import os
import sys
from enum import StrEnum
from pathlib import Path


class CudaLibraryPackage(StrEnum):
    """
    Python packages that provide CUDA runtime shared libraries
    """

    CUBLAS = "nvidia.cublas.lib"
    CUDNN = "nvidia.cudnn.lib"


class CudaEnvironmentVariable(StrEnum):
    """
    Environment variables used to configure CUDA library loading
    """

    LIBRARY_PATH = "LD_LIBRARY_PATH"
    RESTARTED = "DEADLOCK_TRANSCRIBE_CUDA_READY"


def configure_cuda_libraries() -> None:
    """
    Restart Python with packaged CUDA library paths when they are available
    """
    if os.name != "posix" or os.environ.get(CudaEnvironmentVariable.RESTARTED) == "1":
        return
    library_paths = _cuda_library_paths()
    if not library_paths:
        return
    environment = dict(os.environ)
    existing_paths = environment.get(CudaEnvironmentVariable.LIBRARY_PATH, "")
    environment[CudaEnvironmentVariable.LIBRARY_PATH] = ":".join(
        [*library_paths, existing_paths] if existing_paths else library_paths
    )
    environment[CudaEnvironmentVariable.RESTARTED] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], environment)


def _cuda_library_paths() -> list[str]:
    paths: list[str] = []
    for package in CudaLibraryPackage:
        try:
            module = importlib.import_module(package)
        except ModuleNotFoundError:
            return []
        module_paths = getattr(module, "__path__", ())
        for module_path in module_paths:
            path = Path(module_path)
            if path.is_dir():
                paths.append(str(path))
    return paths
