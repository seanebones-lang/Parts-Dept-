import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.graph.queries import inventory_queries
from backend.email.processor import email_processor
from backend.llm.router import llm_router
from loguru import logger


async def test_inventory():
    logger.info("Testing inventory queries...")
    
    try:
        locations = await inventory_queries.get_all_locations()
        logger.info(f"Found {len(locations)} locations")
        
        if locations:
            parts = await inventory_queries.find_parts_by_name("brake")
            logger.info(f"Found {len(parts)} parts matching 'brake'")
            
            if parts:
                part_sku = parts[0]['sku']
                inventory = await inventory_queries.check_inventory(part_sku)
                logger.info(f"Inventory for {part_sku}: {inventory}")
        
        low_stock = await inventory_queries.get_low_stock_items()
        logger.info(f"Low stock items: {len(low_stock)}")
        
        logger.info("✓ Inventory system working")
        return True
    
    except Exception as e:
        logger.error(f"✗ Inventory test failed: {e}")
        return False


async def test_llm_router():
    logger.info("Testing LLM router...")
    
    try:
        test_prompt = "What are brake pads?"
        result = await llm_router.generate(test_prompt)
        
        logger.info(f"LLM Response (using {result['model_used']}): {result['response'][:100]}...")
        logger.info("✓ LLM router working")
        return True
    
    except Exception as e:
        logger.error(f"✗ LLM test failed: {e}")
        return False


async def test_email_processing():
    logger.info("Testing email processing...")
    
    try:
        test_email = {
            "subject": "Need brake pads",
            "from": "customer@test.com",
            "body": "Hi, I need front brake pads for my Honda Civic. Do you have them in stock at your downtown location?"
        }
        
        result = await email_processor.process_email(test_email)
        
        logger.info(f"Intent: {result['classification']['intent']}")
        logger.info(f"Confidence: {result['classification']['confidence']}")
        logger.info(f"Requires human: {result['response_data']['requires_human']}")
        
        if not result['response_data']['requires_human']:
            logger.info(f"Response preview: {result['response_data']['response'][:100]}...")
        
        logger.info("✓ Email processing working")
        return True
    
    except Exception as e:
        logger.error(f"✗ Email processing test failed: {e}")
        return False


async def main():
    from backend.graph.connection import graph_db
    from backend.rag.vectorstore import vector_store
    
    logger.info("Starting system tests...")
    
    try:
        await graph_db.connect()
        logger.info("✓ Connected to Neo4j")
        
        await vector_store.initialize()
        logger.info("✓ Connected to Qdrant")
        
        results = {
            "inventory": await test_inventory(),
            "llm": await test_llm_router(),
            "email": await test_email_processing()
        }
        
        logger.info("\n" + "="*50)
        logger.info("TEST RESULTS:")
        for component, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{component.upper()}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            logger.info("\n✓ All tests passed!")
        else:
            logger.warning("\n✗ Some tests failed")
        
        await graph_db.close()
        
        return 0 if all_passed else 1
    
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

