"""
Demo script for testing the complete RAG system
Run this to verify everything works without AWS credits
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.paper_parser import create_paper_database, demo_paper_processing
from rag.indexer import RetrievalInterface
from backend.tools.sm_client import create_clients


async def test_complete_rag_system():
    """Test the complete RAG system end-to-end"""
    print("🚀 Testing Complete RAG System")
    print("=" * 60)
    
    # Step 1: Initialize components
    print("\n1️⃣  Initializing components...")
    
    # Create mock clients
    reasoning_client, embedding_client = create_clients()
    print("✅ Mock NIM clients created")
    
    # Create retrieval interface
    retrieval = RetrievalInterface(use_local=True)
    print("✅ Local RAG indexer created")
    
    # Create paper database
    paper_db = create_paper_database()
    print("✅ Mock paper database created")
    
    # Step 2: Index sample papers
    print("\n2️⃣  Indexing sample papers...")
    
    papers = paper_db.get_available_papers()
    for paper_info in papers:
        paper_content = paper_db.get_paper_content(paper_info['id'])
        if paper_content:
            success = await retrieval.index_paper(
                paper_id=paper_info['id'],
                content=paper_content['content'],
                title=paper_content['title']
            )
            if success:
                print(f"✅ Indexed: {paper_content['title']}")
            else:
                print(f"❌ Failed to index: {paper_content['title']}")
    
    # Step 3: Index style patterns
    print("\n3️⃣  Indexing style patterns...")
    
    style_success = await retrieval.index_styles()
    if style_success:
        print("✅ Style patterns indexed")
    else:
        print("❌ Failed to index style patterns")
    
    # Step 4: Test fact retrieval
    print("\n4️⃣  Testing fact retrieval...")
    
    test_queries = [
        "attention mechanism in neural networks",
        "residual learning and deep networks", 
        "transformer architecture",
        "image classification with ResNet"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        facts = await retrieval.retrieve_facts(query, k=3)
        
        if facts:
            print(f"   Found {len(facts)} relevant facts:")
            for i, fact in enumerate(facts, 1):
                print(f"   {i}. {fact['text'][:100]}... (score: {fact.get('score', 0):.3f})")
        else:
            print("   No facts found")
    
    # Step 5: Test style retrieval
    print("\n5️⃣  Testing style retrieval...")
    
    style_queries = [
        "opening conversation patterns",
        "technical explanations",
        "audience engagement techniques"
    ]
    
    for query in style_queries:
        print(f"\n🎨 Style Query: '{query}'")
        styles = await retrieval.retrieve_styles(query, k=2)
        
        if styles:
            print(f"   Found {len(styles)} style patterns:")
            for i, style in enumerate(styles, 1):
                style_name = style.get('style_name', 'unknown')
                section = style.get('section', 'general')
                print(f"   {i}. {style_name} - {section} (score: {style.get('score', 0):.3f})")
        else:
            print("   No style patterns found")
    
    # Step 6: Test NIM clients with RAG context
    print("\n6️⃣  Testing NIM clients with RAG context...")
    
    # Get some facts for context
    context_facts = await retrieval.retrieve_facts("transformer attention mechanism", k=2)
    context_text = "\n".join([fact['text'][:200] for fact in context_facts])
    
    # Test reasoning client
    print("\n🤖 Testing Reasoning Client...")
    messages = [{"role": "user", "content": "Based on this context about transformers, explain the key innovation: " + context_text}]
    reasoning_response = await reasoning_client.generate(
        messages=messages,
        response_type="outline",
        max_tokens=150
    )
    
    if reasoning_response and 'choices' in reasoning_response:
        generated_text = reasoning_response['choices'][0]['message']['content']
        print(f"Generated: {generated_text[:200]}...")
    else:
        print("❌ Reasoning client failed")
    
    # Test embedding client
    print("\n🔗 Testing Embedding Client...")
    embedding_response = await embedding_client.embed([
        "transformer architecture with attention",
        "deep residual learning"
    ])
    
    if embedding_response and 'data' in embedding_response:
        print(f"✅ Generated {len(embedding_response['data'])} embeddings")
        print(f"   Embedding dimensions: {len(embedding_response['data'][0]['embedding'])}")
    else:
        print("❌ Embedding client failed")
    
    # Step 7: Test complete pipeline
    print("\n7️⃣  Testing complete pipeline...")
    
    # Simulate podcast generation request
    paper_id = papers[0]['id'] if papers else None
    
    if paper_id:
        print(f"\n📻 Simulating podcast generation for: {papers[0]['title']}")
        
        # Step 7a: Get paper facts
        paper_facts = await retrieval.retrieve_facts(
            "main concepts and contributions", 
            k=5, 
            paper_id=paper_id
        )
        print(f"   Retrieved {len(paper_facts)} key facts")
        
        # Step 7b: Get style patterns
        style_patterns = await retrieval.retrieve_styles(
            "technical explanation patterns", 
            style_name="tech_energetic", 
            k=2
        )
        print(f"   Retrieved {len(style_patterns)} style patterns")
        
        # Step 7c: Generate outline
        facts_context = "\n".join([f"- {fact['text'][:150]}" for fact in paper_facts])
        style_context = "\n".join([f"Style: {s['text'][:100]}" for s in style_patterns])
        
        messages = [{"role": "user", "content": f"Create a podcast episode outline based on these research findings:\n\nFacts:\n{facts_context}\n\nStyle Guide:\n{style_context}"}]
        outline_response = await reasoning_client.generate(
            messages=messages,
            response_type="outline"
        )
        
        if outline_response:
            print("✅ Generated podcast outline")
            print(f"   Outline preview: {str(outline_response)[:150]}...")
        else:
            print("❌ Failed to generate outline")
    
    print("\n" + "=" * 60)
    print("🎉 RAG System Test Complete!")
    print("\nNext steps:")
    print("  1. Run the agents to generate a full podcast")
    print("  2. Test the FastAPI backend")
    print("  3. Build the Streamlit frontend")
    print("  4. Record a demo for hackathon submission")


if __name__ == "__main__":
    # Set up event loop for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_complete_rag_system())