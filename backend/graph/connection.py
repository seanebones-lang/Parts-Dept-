from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Optional, Dict, List, Any
from loguru import logger

from backend.config import settings


class GraphDatabase:
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self.database = settings.neo4j_database
    
    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            await self.driver.verify_connectivity()
            logger.info("Neo4j connection established")
            await self.initialize_schema()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def initialize_schema(self):
        constraints_and_indexes = [
            "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT part_sku IF NOT EXISTS FOR (p:Part) REQUIRE p.sku IS UNIQUE",
            "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE",
            "CREATE INDEX part_name IF NOT EXISTS FOR (p:Part) ON (p.name)",
            "CREATE INDEX location_name IF NOT EXISTS FOR (l:Location) ON (l.name)",
        ]
        
        async with self.driver.session(database=self.database) as session:
            for query in constraints_and_indexes:
                try:
                    await session.run(query)
                    logger.debug(f"Executed: {query}")
                except Exception as e:
                    logger.warning(f"Schema initialization warning: {e}")
        
        logger.info("Neo4j schema initialized")
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        if not self.driver:
            raise RuntimeError("Database not connected")
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    
    async def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        if not self.driver:
            raise RuntimeError("Database not connected")
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            await session.close()
            return records


graph_db = GraphDatabase()

