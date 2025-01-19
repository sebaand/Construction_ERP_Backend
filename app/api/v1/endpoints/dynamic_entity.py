from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.services.dynamic_entity_service import DynamicEntityService
from app.schemas.dynamic_entity import EntitySchema, EntityInstance, CompanyWorkflow

router = APIRouter()

@router.post("/companies/{company_id}/schemas")
async def create_schema(
    company_id: str,
    schema: EntitySchema,
    service: DynamicEntityService = Depends()
) -> Dict:
    """Create a new entity schema for a company"""
    return await service.create_schema(company_id, schema)

@router.get("/companies/{company_id}/schemas")
async def list_schemas(
    company_id: str,
    service: DynamicEntityService = Depends()
) -> List[Dict]:
    """List all schemas for a company"""
    return await service.list_schemas(company_id)

@router.post("/companies/{company_id}/entities")
async def create_entity(
    company_id: str,
    schema_id: str,
    data: Dict[str, Any],
    relationships: Dict[str, str] = None,
    service: DynamicEntityService = Depends()
) -> Dict:
    """Create a new entity instance"""
    try:
        return await service.create_entity(
            company_id, 
            schema_id, 
            data, 
            relationships
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/companies/{company_id}/entities/{entity_id}")
async def get_entity(
    company_id: str,
    entity_id: str,
    service: DynamicEntityService = Depends()
) -> Dict:
    """Get an entity by ID"""
    entity = await service.get_entity(company_id, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

@router.get("/companies/{company_id}/entities/{entity_id}/related")
async def get_related_entities(
    company_id: str,
    entity_id: str,
    relationship_type: str = None,
    service: DynamicEntityService = Depends()
) -> List[Dict]:
    """Get related entities"""
    return await service.get_related_entities(
        company_id, 
        entity_id, 
        relationship_type
    )