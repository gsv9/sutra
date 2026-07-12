"""
Compatibility wrapper for the Qualcomm Phi-3 backend.

The rest of the codebase expects a `QualcommPhi3Client` class in this
module, so we re-export the actual Snapdragon NPU implementation here.
"""

from __future__ import annotations

from .qualcomm_phi3_npu import QualcommPhi3NPUClient as QualcommPhi3Client

