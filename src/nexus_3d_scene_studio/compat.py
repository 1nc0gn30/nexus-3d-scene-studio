"""Cross-platform compatibility and system runtime abstraction layer for Nexus 3D Scene Studio.

Supports Linux, Termux Android, macOS, and Windows with zero external runtime dependencies.
"""

from __future__ import annotations

import ctypes
import dataclasses
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import typing
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclasses.dataclass(frozen=True)
class PlatformInfo:
    """Immutable platform metadata descriptor."""
    os_name: str
    system: str
    release: str
    architecture: str
    python_version: str
    is_linux: bool
    is_macos: bool
    is_windows: bool
    is_termux: bool
    is_64bit: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert platform info to dictionary representation."""
        return dataclasses.asdict(self)


def is_linux() -> bool:
    """Return True if running on a Linux-based operating system (including Termux)."""
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    """Return True if running on Apple macOS / Darwin."""
    return sys.platform == "darwin"


def is_windows() -> bool:
    """Return True if running on Microsoft Windows."""
    return sys.platform in ("win32", "cygwin")


def is_termux() -> bool:
    """Return True if running inside Termux on Android."""
    if "TERMUX_VERSION" in os.environ:
        return True
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    return os.path.exists("/data/data/com.termux/files/usr")


def get_platform_info() -> PlatformInfo:
    """Retrieve comprehensive platform runtime information."""
    sys_name = platform.system()
    machine = platform.machine()
    is_64 = sys.maxsize > 2**32
    termux_flag = is_termux()
    win_flag = is_windows()
    mac_flag = is_macos()
    linux_flag = is_linux()

    return PlatformInfo(
        os_name="termux" if termux_flag else sys_name.lower(),
        system=sys_name,
        release=platform.release(),
        architecture=machine,
        python_version=platform.python_version(),
        is_linux=linux_flag,
        is_macos=mac_flag,
        is_windows=win_flag,
        is_termux=termux_flag,
        is_64bit=is_64,
    )


def setup_utf8_console() -> bool:
    """Configure stdout and stderr for UTF-8 encoding across Windows, Linux, Termux, and macOS.

    Returns:
        True if UTF-8 encoding was successfully confirmed or reconfigured.
    """
    success = True

    # Reconfigure standard streams if available (Python 3.7+)
    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                success = False

    # Windows console code page setup
    if is_windows():
        try:
            # Set Windows console output code page to UTF-8 (65001)
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            try:
                subprocess.run(
                    ["chcp", "65001"],
                    shell=True,
                    capture_output=True,
                    check=False,
                )
            except Exception:
                pass

    return success


def ensure_utf8(text_or_bytes: Union[str, bytes]) -> str:
    """Ensure input is returned as a clean, valid UTF-8 decoded string.

    Args:
        text_or_bytes: String or byte sequence.

    Returns:
        Decoded unicode string with error replacement.
    """
    if isinstance(text_or_bytes, bytes):
        return text_or_bytes.decode("utf-8", errors="replace")
    if isinstance(text_or_bytes, str):
        return text_or_bytes
    return str(text_or_bytes)


def to_posix_path(path_val: Union[str, Path]) -> str:
    """Convert any Windows or native filesystem path to a standard POSIX forward-slash path.

    Args:
        path_val: File path string or Path instance.

    Returns:
        Forward-slash normalized string path.
    """
    if isinstance(path_val, Path):
        return path_val.as_posix()
    path_str = str(path_val)
    return path_str.replace("\\", "/")


def normalize_path(path_val: Union[str, Path]) -> Path:
    """Expand user tilde `~` and resolve to absolute Path."""
    return Path(path_val).expanduser().resolve()


def atomic_write_text(
    filepath: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> Path:
    """Atomically write text content to a file via a temporary file in the same directory.

    Guarantees no half-written or corrupted files on power/process interruption.

    Args:
        filepath: Target destination file path.
        content: Text content to write.
        encoding: File encoding (default 'utf-8').
        errors: Error handling scheme for encoding.

    Returns:
        Path to the successfully written file.
    """
    target = Path(filepath).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    temp_fd, temp_path_str = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.tmp_",
    )
    temp_path = Path(temp_path_str)

    try:
        with open(temp_fd, "w", encoding=encoding, errors=errors) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replacement on POSIX and modern Windows NTFS
        temp_path.replace(target)
        return target
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def atomic_write_bytes(
    filepath: Union[str, Path],
    data: bytes,
) -> Path:
    """Atomically write binary data to a file via a temporary file in the same directory.

    Args:
        filepath: Target destination file path.
        data: Binary byte sequence to write.

    Returns:
        Path to the successfully written file.
    """
    target = Path(filepath).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    temp_fd, temp_path_str = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.tmp_",
    )
    temp_path = Path(temp_path_str)

    try:
        with open(temp_fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        temp_path.replace(target)
        return target
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def open_in_browser(target: Union[str, Path], background: bool = False) -> bool:
    """Launch a URL or HTML file in the default browser across all supported OS environments.

    Args:
        target: URL string or local file path.
        background: If True, request background tab where supported.

    Returns:
        True if browser launch command was initiated successfully, False otherwise.
    """
    target_str = str(target)
    if isinstance(target, Path) or (not target_str.startswith("http://") and not target_str.startswith("https://") and not target_str.startswith("file://")):
        path_obj = Path(target_str).resolve()
        target_str = path_obj.as_uri()

    # Termux Android handling
    if is_termux():
        for cmd in ("termux-open-url", "termux-open", "xdg-open"):
            if shutil.which(cmd):
                try:
                    subprocess.Popen(
                        [cmd, target_str],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except Exception:
                    pass

    # Windows handling
    if is_windows():
        try:
            if hasattr(os, "startfile"):
                os.startfile(target_str)  # type: ignore[attr-defined]
                return True
        except Exception:
            pass

    # macOS handling
    if is_macos():
        if shutil.which("open"):
            try:
                args = ["open", "-g", target_str] if background else ["open", target_str]
                subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                pass

    # Linux standard handling
    if is_linux():
        if shutil.which("xdg-open"):
            try:
                subprocess.Popen(
                    ["xdg-open", target_str],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                pass

    # Fallback to standard library webbrowser module
    try:
        return webbrowser.open(target_str, new=2, autoraise=not background)
    except Exception:
        return False


def get_system_diagnostics() -> Dict[str, Any]:
    """Gather diagnostic runtime metrics for system audits and optimization telemetry.

    Returns:
        Structured dictionary with OS, CPU, memory, disk, and Python diagnostics.
    """
    pinfo = get_platform_info()
    cwd_path = Path.cwd()
    temp_dir = tempfile.gettempdir()

    # Disk usage stats
    disk_total = 0
    disk_free = 0
    try:
        usage = shutil.disk_usage(cwd_path)
        disk_total = usage.total
        disk_free = usage.free
    except Exception:
        pass

    # Memory approximation (pure stdlib)
    total_ram_mb: Optional[float] = None
    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            total_ram_mb = round((pages * page_size) / (1024 * 1024), 2)
        except Exception:
            pass

    return {
        "platform": pinfo.to_dict(),
        "cpu_count": os.cpu_count() or 1,
        "total_ram_mb": total_ram_mb,
        "disk_free_gb": round(disk_free / (1024**3), 2) if disk_free else None,
        "disk_total_gb": round(disk_total / (1024**3), 2) if disk_total else None,
        "python_executable": sys.executable,
        "working_directory": to_posix_path(cwd_path),
        "temp_directory": to_posix_path(temp_dir),
        "stdio_encoding": {
            "stdout": getattr(sys.stdout, "encoding", "unknown"),
            "stderr": getattr(sys.stderr, "encoding", "unknown"),
        },
    }
