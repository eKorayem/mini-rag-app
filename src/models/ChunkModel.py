from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums.DataBaseEnums import DataBaseEnums
from bson.objectid import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[
            DataBaseEnums.COLLECTION_CHUNK_NAME.value
        ]

    async def create_chunk(self, chunk: DataChunk) -> DataChunk:
        data = chunk.dict(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)

        chunk.id = result.inserted_id
        return chunk

    async def get_chunk(self, chunk_id: str) -> DataChunk | None:
        record = await self.collection.find_one(
            {"_id": ObjectId(chunk_id)}
        )

        if record is None:
            return None

        return DataChunk(**record)

    # batch insert
    async def insert_many_chunks(
        self,
        chunks: list[DataChunk],
        batch_size: int = 100
    ) -> int:

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            operations = [
                InsertOne(
                    chunk.dict(by_alias=True, exclude={"id"})
                )
                for chunk in batch
            ]

            await self.collection.bulk_write(operations)

        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: str):
        result = await self.collection.delete_many({
            "project_id": project_id  # string business ID
        })
        return result.deleted_count