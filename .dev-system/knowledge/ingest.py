"""
M6: Knowledge Ingestion and Validation Pipeline
Automated ingestion of knowledge sources with quality validation
"""

import os
import sys
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from knowledge.knowledge_manager import KnowledgeCorpusManager

class KnowledgeIngestionPipeline:
    """Automated knowledge ingestion with validation"""
    
    def __init__(self):
        self.manager = KnowledgeCorpusManager()
        self.ingestion_log = DEV_SYSTEM_ROOT / "knowledge" / "ingestion.log"
        
    def ingest_from_url(self, url: str, title: str = None, source_type: str = "documentation") -> Optional[str]:
        """Ingest knowledge from URL with validation"""
        
        print(f"📥 Ingesting from URL: {url}")
        
        try:
            # Fetch content
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract text content (simplified)
            content = self._extract_text_content(response.text, response.headers.get('content-type', ''))
            
            if not content or len(content) < 100:
                print(f"❌ Insufficient content from {url}")
                return None
            
            # Generate title if not provided
            if not title:
                title = self._extract_title(response.text, url)
            
            # Validate content quality
            quality_score = self._assess_content_quality(content)
            
            if quality_score < 0.6:
                print(f"⚠️  Low quality content (score: {quality_score:.2f})")
                return None
            
            # Add to corpus
            source_id = self.manager.add_knowledge_source(
                title=title,
                content=content,
                source_url=url,
                source_type=source_type,
                tags=self._extract_tags(content, url)
            )
            
            # Log ingestion
            self._log_ingestion(source_id, url, 'SUCCESS', f'Quality: {quality_score:.2f}')
            
            print(f"✅ Ingested: {title} (quality: {quality_score:.2f})")
            return source_id
            
        except Exception as e:
            error_msg = f"Failed to ingest {url}: {e}"
            print(f"❌ {error_msg}")
            self._log_ingestion(None, url, 'FAILED', error_msg)
            return None
    
    def _extract_text_content(self, html_content: str, content_type: str) -> str:
        """Extract text from HTML or other content"""
        
        # Simple text extraction (in real implementation, use BeautifulSoup)
        if 'html' in content_type.lower():
            # Remove HTML tags (basic)
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            return text.strip()
        else:
            return html_content
    
    def _extract_title(self, html_content: str, url: str) -> str:
        """Extract title from content or URL"""
        
        # Try to find HTML title  
        import re
        title_match = re.search(r'<title>([^<]+)</title>', html_content, re.IGNORECASE)
        
        if title_match:
            return title_match.group(1).strip()
        
        # Fallback to URL-based title
        parsed = urlparse(url)
        return f"Content from {parsed.netloc}"
    
    def _extract_tags(self, content: str, url: str) -> List[str]:
        """Extract relevant tags from content and URL"""
        
        tags = []
        
        # URL-based tags
        parsed = urlparse(url)
        if 'github.com' in parsed.netloc:
            tags.append('github')
        elif 'docs.' in parsed.netloc:
            tags.append('documentation')
        
        # Content-based tags (simple keyword detection)
        content_lower = content.lower()
        
        tech_keywords = {
            'python': 'python',
            'javascript': 'javascript', 
            'react': 'react',
            'ai': 'artificial_intelligence',
            'machine learning': 'machine_learning',
            'api': 'api',
            'kubernetes': 'kubernetes',
            'docker': 'docker'
        }
        
        for keyword, tag in tech_keywords.items():
            if keyword in content_lower:
                tags.append(tag)
        
        return tags[:5]  # Limit to 5 tags
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess content quality score"""
        
        # Simple quality metrics
        score = 1.0
        
        # Length check
        if len(content) < 200:
            score *= 0.5
        elif len(content) > 10000:
            score *= 0.9  # Very long content might be noisy
        
        # Structure indicators
        if '\n' in content:
            score *= 1.1  # Has structure
        
        # Technical content indicators
        tech_indicators = ['api', 'function', 'class', 'method', 'parameter']
        tech_count = sum(1 for indicator in tech_indicators if indicator in content.lower())
        score *= min(1.2, 1.0 + tech_count * 0.05)
        
        return min(1.0, score)
    
    def _log_ingestion(self, source_id: Optional[str], url: str, status: str, details: str):
        """Log ingestion attempt"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'source_id': source_id,
            'url': url,
            'status': status,
            'details': details
        }
        
        with open(self.ingestion_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def batch_ingest_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Batch ingest multiple URLs"""
        
        results = {
            'successful': [],
            'failed': [],
            'total_processed': len(urls)
        }
        
        print(f"📥 Batch ingesting {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n🔄 Processing {i}/{len(urls)}: {url}")
            
            source_id = self.ingest_from_url(url)
            
            if source_id:
                results['successful'].append({'url': url, 'source_id': source_id})
            else:
                results['failed'].append({'url': url, 'error': 'Ingestion failed'})
            
            # Rate limiting
            time.sleep(1)  # Be respectful to servers
        
        print(f"\n📊 Batch ingestion complete:")
        print(f"  ✅ Successful: {len(results['successful'])}")
        print(f"  ❌ Failed: {len(results['failed'])}")
        
        return results

def create_sample_knowledge():
    """Create sample knowledge sources for testing"""
    
    manager = KnowledgeCorpusManager()
    
    # Sample AI/ML knowledge
    ai_knowledge = """
    # AI Development Best Practices
    
    ## Prompt Engineering
    
    Effective prompt engineering requires:
    1. Clear, specific instructions
    2. Examples of desired output
    3. Context and constraints
    4. Iterative refinement based on results
    
    ## Model Selection
    
    Choose models based on:
    - Task complexity (GPT-3.5 for simple, GPT-4 for complex)
    - Cost considerations ($0.002/1K tokens for GPT-3.5)
    - Latency requirements (GPT-3.5 faster)
    - Quality requirements (GPT-4 higher quality)
    
    ## Safety Considerations
    
    Always implement:
    - Rate limiting to prevent abuse
    - Content filtering for safety
    - Cost monitoring and alerts
    - Quality gates for production
    """
    
    # Sample project knowledge (configurable)
    project_name = os.getenv("PROJECT_NAME", "threads-agent")
    project_knowledge = f"""
    # {project_name.title()} Development Guide
    
    ## Architecture
    
    The {project_name} system consists of:
    - Orchestrator: API coordination and task routing
    - Persona Runtime: LangGraph-based content generation
    - Viral Engine: Engagement prediction and optimization
    - Celery Worker: Background task processing
    
    ## Development Workflow
    
    1. Use k3d for local Kubernetes development
    2. Run `just dev-start` to bootstrap environment
    3. Deploy with `just deploy-dev` 
    4. Monitor with `just logs`
    5. Test with `just e2e`
    
    ## Performance Targets
    
    - Content generation: < 30s end-to-end
    - Engagement prediction: < 5s
    - API response time: < 2s
    - Cost per post: < $0.05
    """
    
    # Add sample sources
    sources = [
        {
            'title': 'AI Development Best Practices',
            'content': ai_knowledge,
            'source_type': 'documentation',
            'tags': ['ai', 'best_practices', 'prompt_engineering']
        },
        {
            'title': f'{project_name.title()} Development Guide', 
            'content': project_knowledge,
            'source_type': 'documentation',
            'tags': ['threads_agent', 'architecture', 'development']
        }
    ]
    
    print("📚 Creating sample knowledge sources...")
    
    for source_data in sources:
        source_id = manager.add_knowledge_source(**source_data)
        print(f"  ✅ Added: {source_data['title']} (ID: {source_id})")
    
    return len(sources)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge ingestion pipeline")
    parser.add_argument("--create-samples", action="store_true", help="Create sample knowledge")
    parser.add_argument("--ingest-url", help="Ingest from URL")
    parser.add_argument("--batch-file", help="Batch ingest URLs from file")
    
    args = parser.parse_args()
    
    pipeline = KnowledgeIngestionPipeline()
    
    if args.create_samples:
        count = create_sample_knowledge()
        print(f"✅ Created {count} sample knowledge sources")
        
    elif args.ingest_url:
        source_id = pipeline.ingest_from_url(args.ingest_url)
        if source_id:
            print(f"✅ Ingestion successful: {source_id}")
        else:
            print("❌ Ingestion failed")
            
    elif args.batch_file:
        batch_file = Path(args.batch_file)
        if batch_file.exists():
            urls = batch_file.read_text().strip().split('\n')
            results = pipeline.batch_ingest_urls(urls)
            print(f"📊 Batch results: {len(results['successful'])}/{len(urls)} successful")
        else:
            print(f"❌ Batch file not found: {args.batch_file}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()