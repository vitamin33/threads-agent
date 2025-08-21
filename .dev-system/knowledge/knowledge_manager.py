"""
M6: Knowledge Hygiene and RAG Corpus Management
Curated, source-backed knowledge with freshness tracking and validation
"""

import sys
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

# Simple telemetry decorator (avoiding import issues)
def telemetry_decorator(agent_name: str, event_type: str):
    def decorator(func):
        return func
    return decorator

@dataclass
class KnowledgeSource:
    """Single knowledge source with metadata"""
    id: str
    title: str
    content: str
    source_url: Optional[str]
    source_type: str  # 'documentation', 'article', 'manual', 'api_reference'
    created_at: str
    updated_at: str
    last_validated: str
    validity_score: float  # 0.0-1.0
    tags: List[str]
    chunk_count: int
    broken_links: List[str]

@dataclass
class KnowledgeChunk:
    """Individual knowledge chunk for RAG"""
    chunk_id: str
    source_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]

class KnowledgeCorpusManager:
    """Manages curated RAG corpus with source tracking"""
    
    def __init__(self):
        self.corpus_dir = DEV_SYSTEM_ROOT / "knowledge" / "corpus"
        self.index_dir = DEV_SYSTEM_ROOT / "knowledge" / "index"
        self.cache_dir = DEV_SYSTEM_ROOT / "knowledge" / "cache"
        
        # Create directories
        for dir_path in [self.corpus_dir, self.index_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.sources_file = self.corpus_dir / "sources.json"
        self.chunks_file = self.index_dir / "chunks.json"
        
    def load_sources(self) -> Dict[str, KnowledgeSource]:
        """Load all knowledge sources"""
        if not self.sources_file.exists():
            return {}
        
        try:
            with open(self.sources_file) as f:
                data = json.load(f)
            
            sources = {}
            for source_data in data:
                source = KnowledgeSource(**source_data)
                sources[source.id] = source
            
            return sources
            
        except Exception as e:
            print(f"⚠️  Error loading sources: {e}")
            return {}
    
    def save_sources(self, sources: Dict[str, KnowledgeSource]):
        """Save knowledge sources"""
        source_list = [asdict(source) for source in sources.values()]
        
        with open(self.sources_file, 'w') as f:
            json.dump(source_list, f, indent=2, default=str)
    
    @telemetry_decorator(agent_name="knowledge_manager", event_type="source_add")
    def add_knowledge_source(self, 
                           title: str,
                           content: str,
                           source_url: Optional[str] = None,
                           source_type: str = "manual",
                           tags: List[str] = None) -> str:
        """Add new knowledge source to corpus"""
        
        # Generate source ID
        source_id = hashlib.md5(f"{title}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        # Create source
        source = KnowledgeSource(
            id=source_id,
            title=title,
            content=content,
            source_url=source_url,
            source_type=source_type,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            last_validated=datetime.now().isoformat(),
            validity_score=1.0,  # Start with perfect score
            tags=tags or [],
            chunk_count=0,
            broken_links=[]
        )
        
        # Save source
        sources = self.load_sources()
        sources[source_id] = source
        self.save_sources(sources)
        
        # Create chunks
        chunks = self._create_chunks(source)
        source.chunk_count = len(chunks)
        
        # Update source with chunk count
        sources[source_id] = source
        self.save_sources(sources)
        
        print(f"✅ Added knowledge source: {title} ({len(chunks)} chunks)")
        return source_id
    
    def _create_chunks(self, source: KnowledgeSource, chunk_size: int = 1000, overlap: int = 200) -> List[KnowledgeChunk]:
        """Create chunks from knowledge source"""
        
        content = source.content
        chunks = []
        
        # Simple chunking by character count
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = content.rfind('.', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunk_id = f"{source.id}_chunk_{chunk_index}"
                
                chunk = KnowledgeChunk(
                    chunk_id=chunk_id,
                    source_id=source.id,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    embedding=None,  # Embeddings would be generated here
                    metadata={
                        'source_title': source.title,
                        'source_type': source.source_type,
                        'source_url': source.source_url,
                        'created_at': source.created_at,
                        'tags': source.tags
                    }
                )
                
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap if end < len(content) else end
        
        # Save chunks
        self._save_chunks(chunks)
        
        return chunks
    
    def _save_chunks(self, chunks: List[KnowledgeChunk]):
        """Save chunks to index"""
        existing_chunks = self._load_chunks()
        
        # Add new chunks
        for chunk in chunks:
            existing_chunks[chunk.chunk_id] = chunk
        
        # Save all chunks
        chunk_list = [asdict(chunk) for chunk in existing_chunks.values()]
        
        with open(self.chunks_file, 'w') as f:
            json.dump(chunk_list, f, indent=2, default=str)
    
    def _load_chunks(self) -> Dict[str, KnowledgeChunk]:
        """Load all chunks"""
        if not self.chunks_file.exists():
            return {}
        
        try:
            with open(self.chunks_file) as f:
                data = json.load(f)
            
            chunks = {}
            for chunk_data in data:
                chunk = KnowledgeChunk(**chunk_data)
                chunks[chunk.chunk_id] = chunk
            
            return chunks
            
        except Exception as e:
            print(f"⚠️  Error loading chunks: {e}")
            return {}
    
    @telemetry_decorator(agent_name="knowledge_manager", event_type="validation")
    def validate_sources(self) -> Dict[str, Any]:
        """Validate all knowledge sources for freshness and links"""
        
        sources = self.load_sources()
        validation_results = {
            'total_sources': len(sources),
            'validated_sources': 0,
            'stale_sources': [],
            'broken_links': [],
            'updated_sources': []
        }
        
        print(f"🔍 Validating {len(sources)} knowledge sources...")
        
        for source_id, source in sources.items():
            print(f"  📋 Validating: {source.title}")
            
            # Check freshness (30 days default)
            last_validated = datetime.fromisoformat(source.last_validated)
            if datetime.now() - last_validated > timedelta(days=30):
                validation_results['stale_sources'].append({
                    'id': source_id,
                    'title': source.title,
                    'days_stale': (datetime.now() - last_validated).days
                })
            
            # Check links if source has URL
            if source.source_url:
                link_valid = self._validate_link(source.source_url)
                if not link_valid:
                    validation_results['broken_links'].append({
                        'source_id': source_id,
                        'title': source.title,
                        'url': source.source_url
                    })
                    
                    # Update source with broken link
                    source.broken_links = [source.source_url]
                    source.validity_score *= 0.8  # Reduce validity
            
            # Update last validated
            source.last_validated = datetime.now().isoformat()
            validation_results['validated_sources'] += 1
        
        # Save updated sources
        self.save_sources(sources)
        
        print(f"✅ Validation complete:")
        print(f"  📊 Validated: {validation_results['validated_sources']}")
        print(f"  ⚠️  Stale: {len(validation_results['stale_sources'])}")
        print(f"  🔗 Broken links: {len(validation_results['broken_links'])}")
        
        return validation_results
    
    def _validate_link(self, url: str, timeout: int = 10) -> bool:
        """Validate that a URL is accessible"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except Exception:
            return False
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge corpus (simple text search)"""
        
        chunks = self._load_chunks()
        sources = self.load_sources()
        
        # Simple text matching (in real implementation, use embeddings)
        query_lower = query.lower()
        matches = []
        
        for chunk in chunks.values():
            if query_lower in chunk.content.lower():
                source = sources.get(chunk.source_id)
                
                match = {
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
                    'source_title': source.title if source else 'Unknown',
                    'source_url': source.source_url if source else None,
                    'source_type': source.source_type if source else 'unknown',
                    'last_updated': source.updated_at if source else None,
                    'validity_score': source.validity_score if source else 0.0,
                    'relevance_score': chunk.content.lower().count(query_lower) / len(chunk.content.split())
                }
                
                matches.append(match)
        
        # Sort by relevance score
        matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return matches[:limit]
    
    def get_corpus_stats(self) -> Dict[str, Any]:
        """Get corpus statistics"""
        sources = self.load_sources()
        chunks = self._load_chunks()
        
        # Calculate freshness statistics
        now = datetime.now()
        fresh_sources = 0
        stale_sources = 0
        
        for source in sources.values():
            last_updated = datetime.fromisoformat(source.updated_at)
            days_old = (now - last_updated).days
            
            if days_old <= 30:
                fresh_sources += 1
            else:
                stale_sources += 1
        
        # Calculate validity statistics
        avg_validity = sum(s.validity_score for s in sources.values()) / len(sources) if sources else 0.0
        broken_links = sum(len(s.broken_links) for s in sources.values())
        
        return {
            'total_sources': len(sources),
            'total_chunks': len(chunks),
            'fresh_sources': fresh_sources,
            'stale_sources': stale_sources,
            'avg_validity_score': avg_validity,
            'broken_links': broken_links,
            'source_types': self._count_source_types(sources),
            'corpus_size_mb': self._calculate_corpus_size(chunks)
        }
    
    def _count_source_types(self, sources: Dict[str, KnowledgeSource]) -> Dict[str, int]:
        """Count sources by type"""
        type_counts = {}
        for source in sources.values():
            type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
        return type_counts
    
    def _calculate_corpus_size(self, chunks: Dict[str, KnowledgeChunk]) -> float:
        """Calculate corpus size in MB"""
        total_chars = sum(len(chunk.content) for chunk in chunks.values())
        return total_chars / (1024 * 1024)  # Convert to MB

def main():
    """CLI entry point for knowledge management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Corpus Management")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add source
    add_parser = subparsers.add_parser('add', help='Add knowledge source')
    add_parser.add_argument('title', help='Source title')
    add_parser.add_argument('--content', help='Content text')
    add_parser.add_argument('--file', help='Content from file')
    add_parser.add_argument('--url', help='Source URL')
    add_parser.add_argument('--type', default='manual', help='Source type')
    add_parser.add_argument('--tags', nargs='+', help='Tags')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search knowledge')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Result limit')
    
    # Validate
    validate_parser = subparsers.add_parser('validate', help='Validate sources')
    
    # Stats
    stats_parser = subparsers.add_parser('stats', help='Show corpus statistics')
    
    args = parser.parse_args()
    
    manager = KnowledgeCorpusManager()
    
    if args.command == 'add':
        # Get content
        if args.file:
            content_file = Path(args.file)
            if content_file.exists():
                content = content_file.read_text()
            else:
                print(f"❌ File not found: {args.file}")
                return 1
        elif args.content:
            content = args.content
        else:
            print("❌ Must provide --content or --file")
            return 1
        
        source_id = manager.add_knowledge_source(
            title=args.title,
            content=content,
            source_url=args.url,
            source_type=args.type,
            tags=args.tags
        )
        
        print(f"📋 Source ID: {source_id}")
    
    elif args.command == 'search':
        results = manager.search_knowledge(args.query, args.limit)
        
        print(f"🔍 Search Results for: {args.query}")
        print("=" * 50)
        
        if not results:
            print("No results found")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. **{result['source_title']}**")
            print(f"   Type: {result['source_type']}")
            print(f"   Content: {result['content']}")
            
            if result['source_url']:
                print(f"   Source: {result['source_url']}")
            
            print(f"   Updated: {result['last_updated']}")
            print(f"   Validity: {result['validity_score']:.2f}")
            print(f"   Relevance: {result['relevance_score']:.3f}")
    
    elif args.command == 'validate':
        validation_results = manager.validate_sources()
        
        if validation_results['stale_sources']:
            print(f"\n⚠️  Stale Sources:")
            for stale in validation_results['stale_sources']:
                print(f"  • {stale['title']} ({stale['days_stale']} days old)")
        
        if validation_results['broken_links']:
            print(f"\n🔗 Broken Links:")
            for broken in validation_results['broken_links']:
                print(f"  • {broken['title']}: {broken['url']}")
    
    elif args.command == 'stats':
        stats = manager.get_corpus_stats()
        
        print("📊 Knowledge Corpus Statistics")
        print("=" * 40)
        print(f"Total Sources: {stats['total_sources']}")
        print(f"Total Chunks: {stats['total_chunks']}")
        print(f"Corpus Size: {stats['corpus_size_mb']:.2f} MB")
        print(f"Fresh Sources: {stats['fresh_sources']}")
        print(f"Stale Sources: {stats['stale_sources']}")
        print(f"Avg Validity: {stats['avg_validity_score']:.2f}")
        print(f"Broken Links: {stats['broken_links']}")
        
        if stats['source_types']:
            print(f"\nSource Types:")
            for source_type, count in stats['source_types'].items():
                print(f"  • {source_type}: {count}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()