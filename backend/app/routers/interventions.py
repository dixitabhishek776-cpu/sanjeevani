from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.core.auth import get_current_user

router=APIRouter(prefix="/v1/interventions",tags=["interventions"])
DEFAULTS=[
 {"slug":"grounding-54321","title":"5-4-3-2-1 grounding","indication":"stress","evidence_source":"WHO stress-management self-help materials","content":{"steps":["Name 5 things you can see","Name 4 things you can touch","Name 3 things you can hear","Name 2 things you can smell","Name 1 thing you can taste"]}},
 {"slug":"slow-breathing","title":"Slow breathing","indication":"stress","evidence_source":"WHO stress-management self-help materials","content":{"steps":["Sit comfortably","Breathe in gently","Breathe out slowly","Repeat for a few minutes without forcing the breath"]}},
]
@router.get("")
def list_interventions(db:Session=Depends(get_db),user=Depends(get_current_user)):
    rows=db.query(models.InterventionCatalog).filter(models.InterventionCatalog.active.is_(True)).all()
    if not rows:
        return DEFAULTS
    return [{"slug":r.slug,"title":r.title,"indication":r.indication,"content":r.content,"evidence_source":r.evidence_source} for r in rows]
