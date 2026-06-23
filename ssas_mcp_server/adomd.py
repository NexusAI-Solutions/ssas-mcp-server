"""
Auto-discovery for the Microsoft.AnalysisServices.AdomdClient.dll.

pyadomd requires the ADOMD.NET client library to be on sys.path.
This module searches common install locations (SSMS, Power BI, AMO SDK)
and adds the first match. You can also set the ADOMD_DLL_PATH environment
variable to provide the folder path explicitly.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

_DLL_NAME = "Microsoft.AnalysisServices.AdomdClient.dll"

# Common locations where the DLL is installed alongside Microsoft tooling.
_SEARCH_PATHS = [
    # SQL Server Management Studio 22 (and future versions)
    r"C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE",
    r"C:\Program Files (x86)\Microsoft SQL Server Management Studio 22\Release\Common7\IDE",
    # SQL Server Management Studio 20/21
    r"C:\Program Files\Microsoft SQL Server Management Studio 21\Release\Common7\IDE",
    r"C:\Program Files\Microsoft SQL Server Management Studio 20\Release\Common7\IDE",
    # SQL Server Management Studio 19 and older (different folder structure)
    r"C:\Program Files (x86)\Microsoft SQL Server Management Studio 19\Common7\IDE",
    r"C:\Program Files (x86)\Microsoft SQL Server Management Studio 18\Common7\IDE",
    # Power BI Desktop
    r"C:\Program Files\Microsoft Power BI Desktop\bin",
    r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin",
    # AMO / ADOMD NuGet or MSI installs
    r"C:\Program Files\Microsoft.NET\ADOMD.NET\160",
    r"C:\Program Files\Microsoft.NET\ADOMD.NET\150",
    r"C:\Program Files\Microsoft.NET\ADOMD.NET\140",
    r"C:\Program Files\Microsoft.NET\ADOMD.NET\130",
    # Visual Studio private assemblies
    r"C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\PrivateAssemblies",
    r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\PrivateAssemblies",
    r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\PrivateAssemblies",
]


def find_adomd_path() -> str | None:
    """Return the folder containing the ADOMD.NET DLL, or None if not found.

    Resolution order:
        1. ADOMD_DLL_PATH environment variable (explicit override).
        2. Well-known install locations in _SEARCH_PATHS.

    Returns:
        Absolute folder path, or None.
    """
    # 1. Explicit override via env var
    env_path = os.environ.get("ADOMD_DLL_PATH")
    if env_path:
        dll_file = os.path.join(env_path, _DLL_NAME)
        if os.path.isfile(dll_file):
            return env_path
        if os.path.isdir(env_path):
            logger.warning(
                "%s not found in ADOMD_DLL_PATH (%s). "
                "The directory exists but the DLL may be missing. "
                "Proceeding anyway in case it is loaded by another mechanism.",
                _DLL_NAME,
                env_path,
            )
            return env_path
        logger.warning("ADOMD_DLL_PATH is set but the path does not exist: %s", env_path)

    # 2. Search well-known locations
    for folder in _SEARCH_PATHS:
        dll_file = os.path.join(folder, _DLL_NAME)
        if os.path.isfile(dll_file):
            return folder

    return None


def ensure_adomd_available() -> None:
    """Add the ADOMD.NET DLL folder to sys.path if it is not already present.

    Raises:
        FileNotFoundError: When the DLL cannot be located anywhere.
    """
    path = find_adomd_path()
    if path is None:
        raise FileNotFoundError(
            f"Could not locate {_DLL_NAME}.\n\n"
            "Install one of the following, or set the ADOMD_DLL_PATH environment\n"
            "variable to the folder that contains the DLL:\n"
            "  - SQL Server Management Studio (SSMS)\n"
            "  - Microsoft Analysis Services client libraries (AMO/ADOMD)\n"
            "  - Power BI Desktop\n"
        )

    if path not in sys.path:
        sys.path.insert(0, path)
