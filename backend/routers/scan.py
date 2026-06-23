"""Public scan/orchestrated/sandbox router facade.

This module is kept as a compatibility facade so existing imports of ``routers.scan``
keep working while route registration is split by domain into dedicated modules.
"""

from fastapi import APIRouter

from routers.orchestrated import router as orchestrated_router
from routers.sandbox import router as sandbox_router
from routers.extract import router as extract_router

router = APIRouter()
router.include_router(orchestrated_router)
router.include_router(sandbox_router)
router.include_router(extract_router)
