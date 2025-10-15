import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.graph.queries import inventory_queries
from backend.graph.schema import Location, Part, InventoryItem
from backend.rag.ingestion import document_ingestion
from loguru import logger


async def seed_locations():
    locations = [
        {
            "id": "loc-001",
            "name": "Downtown Service Center",
            "address": "100 Main Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
            "phone": "555-0100",
            "email": "downtown@dealer.com",
            "manager": "John Smith"
        },
        {
            "id": "loc-002",
            "name": "Westside Auto Parts",
            "address": "2500 West Avenue",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62702",
            "phone": "555-0200",
            "email": "westside@dealer.com",
            "manager": "Sarah Johnson"
        },
        {
            "id": "loc-003",
            "name": "Eastside Parts Depot",
            "address": "3800 East Boulevard",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62703",
            "phone": "555-0300",
            "email": "eastside@dealer.com",
            "manager": "Mike Williams"
        },
    ]
    
    for loc_data in locations:
        try:
            location = Location(**loc_data)
            await inventory_queries.create_location(location)
            logger.info(f"Created location: {loc_data['name']}")
        except Exception as e:
            logger.warning(f"Location {loc_data['name']} might already exist: {e}")


async def seed_parts():
    parts = [
        {
            "sku": "BRK-PAD-001",
            "name": "Ceramic Brake Pads - Front",
            "description": "High-performance ceramic brake pads for most sedans",
            "manufacturer": "Brembo",
            "category": "Brakes",
            "list_price": 89.99,
            "cost": 45.00
        },
        {
            "sku": "BRK-PAD-002",
            "name": "Ceramic Brake Pads - Rear",
            "description": "High-performance ceramic brake pads for rear wheels",
            "manufacturer": "Brembo",
            "category": "Brakes",
            "list_price": 79.99,
            "cost": 40.00
        },
        {
            "sku": "OIL-FILTER-001",
            "name": "Premium Oil Filter",
            "description": "High-efficiency oil filter for most vehicles",
            "manufacturer": "Mobil 1",
            "category": "Filters",
            "list_price": 12.99,
            "cost": 6.50
        },
        {
            "sku": "AIR-FILTER-001",
            "name": "Engine Air Filter",
            "description": "Standard engine air filter",
            "manufacturer": "K&N",
            "category": "Filters",
            "list_price": 24.99,
            "cost": 12.50
        },
        {
            "sku": "WIPER-001",
            "name": "Windshield Wiper Blades (Pair)",
            "description": "All-season wiper blades",
            "manufacturer": "Bosch",
            "category": "Accessories",
            "list_price": 34.99,
            "cost": 17.50
        },
        {
            "sku": "BATTERY-001",
            "name": "12V Car Battery",
            "description": "700 CCA automotive battery",
            "manufacturer": "Interstate",
            "category": "Electrical",
            "list_price": 159.99,
            "cost": 95.00
        },
        {
            "sku": "TIRE-001",
            "name": "All-Season Tire 205/55R16",
            "description": "All-season tire for compact and mid-size vehicles",
            "manufacturer": "Michelin",
            "category": "Tires",
            "list_price": 119.99,
            "cost": 75.00
        },
    ]
    
    for part_data in parts:
        try:
            part = Part(**part_data)
            await inventory_queries.create_part(part)
            logger.info(f"Created part: {part_data['name']}")
        except Exception as e:
            logger.warning(f"Part {part_data['sku']} might already exist: {e}")


async def seed_inventory():
    inventory_items = [
        # Downtown location
        {"location_id": "loc-001", "part_sku": "BRK-PAD-001", "quantity": 50, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-001", "part_sku": "BRK-PAD-002", "quantity": 40, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-001", "part_sku": "OIL-FILTER-001", "quantity": 100, "min_stock": 20, "reorder_point": 30},
        {"location_id": "loc-001", "part_sku": "AIR-FILTER-001", "quantity": 75, "min_stock": 15, "reorder_point": 25},
        {"location_id": "loc-001", "part_sku": "WIPER-001", "quantity": 30, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-001", "part_sku": "BATTERY-001", "quantity": 25, "min_stock": 5, "reorder_point": 10},
        {"location_id": "loc-001", "part_sku": "TIRE-001", "quantity": 60, "min_stock": 16, "reorder_point": 20},
        
        # Westside location
        {"location_id": "loc-002", "part_sku": "BRK-PAD-001", "quantity": 35, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-002", "part_sku": "OIL-FILTER-001", "quantity": 80, "min_stock": 20, "reorder_point": 30},
        {"location_id": "loc-002", "part_sku": "AIR-FILTER-001", "quantity": 50, "min_stock": 15, "reorder_point": 25},
        {"location_id": "loc-002", "part_sku": "BATTERY-001", "quantity": 15, "min_stock": 5, "reorder_point": 10},
        
        # Eastside location
        {"location_id": "loc-003", "part_sku": "BRK-PAD-002", "quantity": 25, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-003", "part_sku": "OIL-FILTER-001", "quantity": 90, "min_stock": 20, "reorder_point": 30},
        {"location_id": "loc-003", "part_sku": "WIPER-001", "quantity": 20, "min_stock": 10, "reorder_point": 15},
        {"location_id": "loc-003", "part_sku": "TIRE-001", "quantity": 40, "min_stock": 16, "reorder_point": 20},
    ]
    
    for inv_data in inventory_items:
        try:
            inventory = InventoryItem(**inv_data)
            await inventory_queries.add_inventory(inventory)
            logger.info(f"Added inventory: {inv_data['part_sku']} at {inv_data['location_id']}")
        except Exception as e:
            logger.warning(f"Inventory item might already exist: {e}")


async def seed_rag_documents():
    parts_catalog = [
        {
            "name": "Ceramic Brake Pads - Front",
            "sku": "BRK-PAD-001",
            "description": "High-performance ceramic brake pads for most sedans. Reduced noise and dust.",
            "category": "Brakes",
            "manufacturer": "Brembo",
            "price": 89.99
        },
        {
            "name": "Ceramic Brake Pads - Rear",
            "sku": "BRK-PAD-002",
            "description": "High-performance ceramic brake pads for rear wheels. Compatible with most vehicles.",
            "category": "Brakes",
            "manufacturer": "Brembo",
            "price": 79.99
        },
    ]
    
    faq_data = [
        {
            "question": "What types of brake pads do you carry?",
            "answer": "We carry ceramic, semi-metallic, and organic brake pads from top manufacturers like Brembo, Wagner, and Akebono. Ceramic pads offer the best performance with minimal noise and dust.",
            "category": "products"
        },
        {
            "question": "Do you offer installation services?",
            "answer": "Yes, we offer professional installation services at all our locations. Please call ahead to schedule an appointment.",
            "category": "services"
        },
        {
            "question": "What is your return policy?",
            "answer": "We accept returns within 30 days of purchase with original receipt. Parts must be unused and in original packaging. Some restrictions apply to special order items.",
            "category": "policy"
        },
        {
            "question": "Can I transfer parts between locations?",
            "answer": "Yes, we can transfer parts between our locations. Transfers typically take 1-2 business days. Please contact us to arrange a transfer.",
            "category": "inventory"
        },
    ]
    
    try:
        await document_ingestion.ingest_parts_catalog(parts_catalog)
        logger.info("Ingested parts catalog")
        
        await document_ingestion.ingest_faq(faq_data)
        logger.info("Ingested FAQ data")
    except Exception as e:
        logger.error(f"Error ingesting RAG documents: {e}")


async def main():
    from backend.graph.connection import graph_db
    from backend.rag.vectorstore import vector_store
    
    logger.info("Starting data seeding...")
    
    try:
        await graph_db.connect()
        logger.info("Connected to Neo4j")
        
        await vector_store.initialize()
        logger.info("Connected to Qdrant")
        
        await seed_locations()
        await seed_parts()
        await seed_inventory()
        await seed_rag_documents()
        
        logger.info("Data seeding completed successfully!")
        
        await graph_db.close()
    
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

