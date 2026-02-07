from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")

    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    
    # chunk_project_id: ObjectId
    project_id: str  # business ID (same as Project.project_id)

    
    # To make pydantic ignore ObjectId or any unkown data type.
    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        
        
    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("chunk_project_id", 1)
                ],
                "name": "chunk_project_id_index_1",
                "unique": False
            }
        ]