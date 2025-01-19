from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime
from app.schemas.dynamic_entity import EntitySchema, FieldMapping, WorkflowDefinition
from motor.motor_asyncio import AsyncIOMotorClient


class DynamicEntityService:
    def __init__(self, client: AsyncIOMotorClient):
        self.db = client.Forms
        self.entity_schemas = self.db.entity_schemas
        self.entities = self.db.entities
        self.workflows = self.db.workflows

    async def create_schema(self, company_id: str, schema: EntitySchema) -> Dict:
        """Create a new entity schema for a company"""
        schema_doc = {
            "company_id": company_id,
            "schema_name": schema.schema_name,
            "fields": schema.fields.dict(),
            "relationships": schema.relationships,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        result = await self.entity_schemas.insert_one(schema_doc)
        return {"id": str(result.inserted_id), **schema_doc}

    async def create_workflow(self, workflow: WorkflowDefinition) -> Dict:
        """Create a new workflow with field mappings"""
        workflow_doc = workflow.dict()
        workflow_doc["created_at"] = datetime.now()
        workflow_doc["updated_at"] = datetime.now()
        
        # Validate all schemas exist
        for step in workflow.steps.values():
            schema = await self.entity_schemas.find_one({
                "schema_name": step.schema_name,
                "company_id": workflow.company_id
            })
            if not schema:
                raise ValueError(f"Schema {step.schema_name} not found")
            
            # Validate field mappings
            for mapping in step.field_mappings:
                await self._validate_field_mapping(workflow.company_id, mapping)
        
        result = await self.workflows.insert_one(workflow_doc)
        return {"id": str(result.inserted_id), **workflow_doc}

    async def create_entity(
        self, 
        company_id: str, 
        workflow_id: str,
        step_name: str,
        data: Dict[str, Any]
    ) -> Dict:
        """Create an entity and propagate mapped fields"""
        # Get workflow
        workflow = await self.workflows.find_one({"_id": ObjectId(workflow_id)})
        if not workflow:
            raise ValueError("Workflow not found")
            
        step = workflow["steps"].get(step_name)
        if not step:
            raise ValueError(f"Step {step_name} not found in workflow")
            
        # Get schema
        schema = await self.entity_schemas.find_one({
            "schema_name": step["schema_name"],
            "company_id": company_id
        })
        
        # Validate data against schema
        self._validate_against_schema(schema["fields"], data)
        
        # Create entity
        entity_doc = {
            "company_id": company_id,
            "workflow_id": workflow_id,
            "step_name": step_name,
            "schema_name": step["schema_name"],
            "data": data,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await self.entities.insert_one(entity_doc)
        created_entity = {"id": str(result.inserted_id), **entity_doc}
        
        # Apply field mappings to next steps if they exist
        await self._propagate_mapped_fields(
            company_id,
            workflow_id,
            step_name,
            created_entity
        )
        
        return created_entity

    async def get_entity(self, company_id: str, entity_id: str) -> Optional[Dict]:
        """Retrieve an entity by ID"""
        entity = await self.entities.find_one({
            "_id": ObjectId(entity_id),
            "company_id": company_id
        })
        if entity:
            entity["id"] = str(entity["_id"])
        return entity

    async def get_related_entities(
        self, 
        company_id: str, 
        entity_id: str, 
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all entities related to the given entity"""
        entity = await self.get_entity(company_id, entity_id)
        if not entity:
            return []
        
        relationships = entity["relationships"]
        if relationship_type:
            relationships = {k: v for k, v in relationships.items() 
                           if k == relationship_type}
        
        related_entities = []
        for rel_type, rel_id in relationships.items():
            related = await self.get_entity(company_id, rel_id)
            if related:
                related_entities.append(related)
        
        return related_entities

    def _validate_against_schema(self, schema_fields: Dict, data: Dict):
        """Validate entity data against its schema"""
        for field_name, field_def in schema_fields.items():
            if field_def["required"] and field_name not in data:
                raise ValueError(f"Required field {field_name} is missing")
            
            if field_name in data:
                # Add type validation here based on field_def["field_type"]
                pass

    async def _propagate_mapped_fields(
        self,
        company_id: str,
        workflow_id: str,
        current_step: str,
        source_entity: Dict
    ):
        """Propagate mapped fields to next steps in workflow"""
        workflow = await self.workflows.find_one({"_id": ObjectId(workflow_id)})
        step = workflow["steps"][current_step]
        
        for mapping in step["field_mappings"]:
            if mapping["source_schema"] == source_entity["schema_name"]:
                source_value = source_entity["data"].get(mapping["source_field"])
                if source_value is not None:
                    # Create or update target entity with mapped field
                    await self._update_mapped_field(
                        company_id,
                        workflow_id,
                        mapping["target_schema"],
                        mapping["target_field"],
                        source_value,
                        mapping.get("transformation")
                    )

    async def _validate_field_mapping(self, company_id: str, mapping: FieldMapping):
        """Validate that source and target fields exist in their respective schemas"""
        source_schema = await self.entity_schemas.find_one({
            "schema_name": mapping.source_schema,
            "company_id": company_id
        })
        target_schema = await self.entity_schemas.find_one({
            "schema_name": mapping.target_schema,
            "company_id": company_id
        })
        
        if not source_schema or mapping.source_field not in source_schema["fields"]:
            raise ValueError(f"Invalid source field: {mapping.source_field}")
        if not target_schema or mapping.target_field not in target_schema["fields"]:
            raise ValueError(f"Invalid target field: {mapping.target_field}") 