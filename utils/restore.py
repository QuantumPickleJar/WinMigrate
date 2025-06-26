import os
from typing import List, Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


def generate_restore_script(
    pairs: List[Tuple[str, str]],
    output_path: str,
    program_json: Optional[str] = None,
) -> str:
    """Generate a PowerShell script to restore files and optionally programs."""
    lines = [
        "# WinMigrate Restore Script",
        "$ErrorActionPreference = 'Stop'",
    ]
    for original, backup in pairs:
        if os.path.isdir(backup):
            lines.append(
                f"Copy-Item -Path \"{backup}\" -Destination \"{original}\" -Recurse -Force"
            )
        else:
            lines.append(
                f"Copy-Item -Path \"{backup}\" -Destination \"{original}\" -Force"
            )
    if program_json:
        lines.append("")
        lines.append("# Attempt program reinstalls")
        lines.append(f"$programs = Get-Content \"{program_json}\" | ConvertFrom-Json")
        lines.append("foreach ($p in $programs) {")
        lines.append("    if ($p.url) {")
        lines.append(
            "        try { Invoke-WebRequest -Uri $p.url -OutFile \"$env:TEMP\\$($p.name).exe\"; Start-Process \"$env:TEMP\\$($p.name).exe\" -Wait }"
        )
        lines.append(
            "        catch { Write-Host \"Failed to install $($p.name): $_\" }"
        )
        lines.append("    }")
        lines.append("}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Restore script saved to %s", output_path)
    return output_path
