"""
Map management router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.app.models.database import get_db, MapData

router = APIRouter()


@router.get("")
async def list_maps(db: Session = Depends(get_db)):
    maps = db.query(MapData).all()
    return [{"id": m.id, "name": m.name, "resolution_m": m.resolution_m,
             "width": m.width, "height": m.height, "is_default": m.is_default,
             "created_at": m.created_at} for m in maps]


@router.post("")
async def upload_map(map_data: dict, db: Session = Depends(get_db)):
    m = MapData(
        name=map_data["name"],
        description=map_data.get("description"),
        resolution_m=map_data.get("resolution_m", 0.05),
        width=map_data["width"],
        height=map_data["height"],
        origin_x=map_data.get("origin_x", 0.0),
        origin_y=map_data.get("origin_y", 0.0),
        grid_data=map_data["grid_data"]
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "name": m.name}


@router.get("/{map_id}")
async def get_map(map_id: int, db: Session = Depends(get_db)):
    m = db.query(MapData).filter(MapData.id == map_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    return {
        "id": m.id, "name": m.name, "description": m.description,
        "resolution_m": m.resolution_m, "width": m.width, "height": m.height,
        "origin_x": m.origin_x, "origin_y": m.origin_y,
        "grid_data": m.grid_data, "is_default": m.is_default
    }
