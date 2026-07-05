from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Optional
from app.core.dependencies import get_current_user  # type: ignore
from app.services.pest_analysis_service import run_pest_analysis  # type: ignore
from app.services.translation_util import translate_response  # type: ignore

router = APIRouter(prefix="/pest-analysis", tags=["Pest Analysis"])


class PestAnalysisRequest(BaseModel):
    field_id: str
    lang: Optional[str] = "en"


@router.post("/run")
async def pest_analysis_run(
    body: PestAnalysisRequest,
    current_user: dict = Depends(get_current_user),  # type: ignore
):
    """Run automated pest / stress analysis for a registered field."""
    result = await run_pest_analysis(body.field_id, lang=body.lang or "en")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Auto-translate full response to Hindi if requested
    lang = body.lang or "en"
    if lang.startswith("hi"):
        result = translate_response(result, target_lang="hi")

    return result
