from typing import List, Dict, Any, Optional
from loguru import logger

from backend.graph.connection import graph_db
from backend.graph.schema import Location, Part, Department, Supplier, InventoryItem


class InventoryQueries:
    
    @staticmethod
    async def create_location(location: Location) -> Dict:
        query = """
        CREATE (l:Location {
            id: $id,
            name: $name,
            address: $address,
            city: $city,
            state: $state,
            zip_code: $zip_code,
            phone: $phone,
            email: $email,
            manager: $manager,
            created_at: datetime()
        })
        RETURN l
        """
        result = await graph_db.execute_write(query, location.model_dump())
        return result[0]['l'] if result else None
    
    @staticmethod
    async def create_part(part: Part) -> Dict:
        query = """
        MERGE (p:Part {sku: $sku})
        SET p.name = $name,
            p.description = $description,
            p.manufacturer = $manufacturer,
            p.category = $category,
            p.list_price = $list_price,
            p.cost = $cost,
            p.weight = $weight,
            p.dimensions = $dimensions,
            p.updated_at = datetime()
        RETURN p
        """
        result = await graph_db.execute_write(query, part.model_dump())
        return result[0]['p'] if result else None
    
    @staticmethod
    async def create_department(department: Department, location_id: str) -> Dict:
        query = """
        MATCH (l:Location {id: $location_id})
        CREATE (d:Department {
            id: $id,
            name: $name,
            description: $description,
            contact_email: $contact_email
        })
        CREATE (l)-[:HAS_DEPARTMENT]->(d)
        RETURN d
        """
        params = department.model_dump()
        params['location_id'] = location_id
        result = await graph_db.execute_write(query, params)
        return result[0]['d'] if result else None
    
    @staticmethod
    async def add_inventory(inventory: InventoryItem) -> Dict:
        query = """
        MATCH (l:Location {id: $location_id})
        MATCH (p:Part {sku: $part_sku})
        MERGE (l)-[r:HAS_INVENTORY]->(p)
        SET r.quantity = $quantity,
            r.min_stock = $min_stock,
            r.max_stock = $max_stock,
            r.reorder_point = $reorder_point,
            r.last_updated = datetime($last_updated)
        RETURN l, r, p
        """
        params = inventory.model_dump()
        params['last_updated'] = inventory.last_updated.isoformat()
        result = await graph_db.execute_write(query, params)
        return result[0] if result else None
    
    @staticmethod
    async def check_inventory(part_sku: str, location_id: Optional[str] = None) -> List[Dict]:
        if location_id:
            query = """
            MATCH (l:Location {id: $location_id})-[r:HAS_INVENTORY]->(p:Part {sku: $part_sku})
            RETURN l.name as location, l.id as location_id, p.sku as sku, 
                   p.name as part_name, r.quantity as quantity, 
                   r.min_stock as min_stock, p.list_price as price
            """
            params = {"location_id": location_id, "part_sku": part_sku}
        else:
            query = """
            MATCH (l:Location)-[r:HAS_INVENTORY]->(p:Part {sku: $part_sku})
            RETURN l.name as location, l.id as location_id, p.sku as sku,
                   p.name as part_name, r.quantity as quantity,
                   r.min_stock as min_stock, p.list_price as price
            ORDER BY r.quantity DESC
            """
            params = {"part_sku": part_sku}
        
        result = await graph_db.execute_query(query, params)
        return result
    
    @staticmethod
    async def find_parts_by_name(search_term: str, limit: int = 10) -> List[Dict]:
        query = """
        MATCH (p:Part)
        WHERE toLower(p.name) CONTAINS toLower($search_term) 
           OR toLower(p.description) CONTAINS toLower($search_term)
           OR p.sku CONTAINS $search_term
        RETURN p.sku as sku, p.name as name, p.description as description,
               p.category as category, p.list_price as price
        LIMIT $limit
        """
        result = await graph_db.execute_query(query, {"search_term": search_term, "limit": limit})
        return result
    
    @staticmethod
    async def get_low_stock_items(location_id: Optional[str] = None) -> List[Dict]:
        if location_id:
            query = """
            MATCH (l:Location {id: $location_id})-[r:HAS_INVENTORY]->(p:Part)
            WHERE r.quantity <= r.reorder_point
            RETURN l.name as location, p.sku as sku, p.name as part_name,
                   r.quantity as current_quantity, r.reorder_point as reorder_point,
                   r.min_stock as min_stock
            ORDER BY r.quantity ASC
            """
            params = {"location_id": location_id}
        else:
            query = """
            MATCH (l:Location)-[r:HAS_INVENTORY]->(p:Part)
            WHERE r.quantity <= r.reorder_point
            RETURN l.name as location, l.id as location_id, p.sku as sku, 
                   p.name as part_name, r.quantity as current_quantity,
                   r.reorder_point as reorder_point, r.min_stock as min_stock
            ORDER BY r.quantity ASC
            """
            params = {}
        
        result = await graph_db.execute_query(query, params)
        return result
    
    @staticmethod
    async def transfer_inventory(from_location_id: str, to_location_id: str, 
                                 part_sku: str, quantity: int) -> Dict:
        query = """
        MATCH (from:Location {id: $from_location_id})-[r1:HAS_INVENTORY]->(p:Part {sku: $part_sku})
        MATCH (to:Location {id: $to_location_id})-[r2:HAS_INVENTORY]->(p)
        WHERE r1.quantity >= $quantity
        SET r1.quantity = r1.quantity - $quantity,
            r2.quantity = r2.quantity + $quantity,
            r1.last_updated = datetime(),
            r2.last_updated = datetime()
        CREATE (from)-[:TRANSFERRED {
            part_sku: $part_sku,
            quantity: $quantity,
            timestamp: datetime()
        }]->(to)
        RETURN from.name as from_location, to.name as to_location, 
               p.name as part_name, $quantity as quantity_transferred
        """
        params = {
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "part_sku": part_sku,
            "quantity": quantity
        }
        result = await graph_db.execute_write(query, params)
        return result[0] if result else None
    
    @staticmethod
    async def get_all_locations() -> List[Dict]:
        query = """
        MATCH (l:Location)
        RETURN l.id as id, l.name as name, l.city as city, 
               l.state as state, l.phone as phone, l.email as email
        ORDER BY l.name
        """
        result = await graph_db.execute_query(query)
        return result
    
    @staticmethod
    async def create_supplier(supplier: Supplier) -> Dict:
        query = """
        CREATE (s:Supplier {
            id: $id,
            name: $name,
            contact_name: $contact_name,
            email: $email,
            phone: $phone,
            lead_time_days: $lead_time_days,
            created_at: datetime()
        })
        RETURN s
        """
        result = await graph_db.execute_write(query, supplier.model_dump())
        return result[0]['s'] if result else None
    
    @staticmethod
    async def link_supplier_to_part(supplier_id: str, part_sku: str, cost: float, 
                                    lead_time_days: int) -> Dict:
        query = """
        MATCH (s:Supplier {id: $supplier_id})
        MATCH (p:Part {sku: $part_sku})
        MERGE (s)-[r:SUPPLIES]->(p)
        SET r.cost = $cost,
            r.lead_time_days = $lead_time_days,
            r.updated_at = datetime()
        RETURN s, r, p
        """
        params = {
            "supplier_id": supplier_id,
            "part_sku": part_sku,
            "cost": cost,
            "lead_time_days": lead_time_days
        }
        result = await graph_db.execute_write(query, params)
        return result[0] if result else None


inventory_queries = InventoryQueries()

