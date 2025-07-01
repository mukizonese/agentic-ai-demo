import logging
from agents.product_agent import ProductAppAgent
from agents.support_agent import SupportAppAgent

async def initialize_vector_data(llm_service, vector_service):
    """Fetch all products and support articles and add them to the vector DB."""
    logger = logging.getLogger("VectorDataLoader")
    logger.info("Initializing vector database with sample data...")
    product_agent = ProductAppAgent(llm_service)
    support_agent = SupportAppAgent(llm_service)
    # Fetch all products
    products = await product_agent.get_all_products()
    product_docs = []
    for product in products:
        product_docs.append({
            "id": f"product_{product.get('id')}",
            "title": product.get("name", ""),
            "content": f"{product.get('name', '')} - {product.get('description', '')}",
            "source": "Product Catalog"
        })
    # Fetch all support articles
    support_articles = await support_agent.get_all_support_articles()
    support_docs = []
    for article in support_articles:
        support_docs.append({
            "id": f"support_{article.get('id')}",
            "title": article.get("title", ""),
            "content": f"{article.get('title', '')} - {article.get('content', '')}",
            "source": "Support Articles"
        })
    # Add to vector DB
    await vector_service.add_documents(product_docs + support_docs)
    logger.info(f"Successfully added {len(product_docs) + len(support_docs)} documents to vector database") 