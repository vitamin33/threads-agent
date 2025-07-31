# 💻 Usage Examples

This guide provides comprehensive examples of how to use the Achievement Collector System for various scenarios.

## Basic Usage Examples

### 1. Analyze a Single Repository

```python
import asyncio
from services.historical_pr_analyzer import HistoricalPRAnalyzer

async def analyze_repository():
    """Analyze a single GitHub repository."""
    
    # Initialize with your GitHub token
    analyzer = HistoricalPRAnalyzer(github_token="your_github_token")
    
    # Analyze a repository
    results = await analyzer.analyze_repository_history("microsoft/typescript")
    
    # Print summary
    print(f"Repository Analysis Results:")
    print(f"  Total PRs: {results['total_prs']}")
    print(f"  Analyzed PRs: {results['analyzed_prs']}")
    print(f"  High Impact PRs: {results['high_impact_prs']}")
    print(f"  Total Additions: {results['total_additions']:,}")
    print(f"  Total Deletions: {results['total_deletions']:,}")
    
    # Analyze individual high-impact PRs
    print(f"\nTop 5 High-Impact PRs:")
    for i, pr in enumerate(results['pr_analyses'][:5]):
        if pr.get('business_value', {}).get('impact') == 'HIGH':
            print(f"  {i+1}. PR #{pr['number']}: {pr['title']}")
            print(f"     Value: {pr['business_value']['value']}")
            print(f"     Impact: {pr['business_value']['impact']}")
    
    return results

# Run the analysis
asyncio.run(analyze_repository())
```

### 2. Generate Complete Portfolio

```python
import asyncio
from pipeline.end_to_end_integration import EndToEndPipeline

async def generate_complete_portfolio():
    """Generate a complete professional portfolio."""
    
    pipeline = EndToEndPipeline()
    
    # Repositories to analyze (can be multiple)
    repositories = [
        "facebook/react",
        "microsoft/vscode", 
        "your-username/your-project"
    ]
    
    all_results = []
    
    for repo in repositories:
        print(f"🔍 Analyzing {repo}...")
        
        try:
            result = await pipeline.run_complete_pipeline(repo)
            all_results.append({
                "repository": repo,
                "result": result
            })
            
            print(f"  ✅ Success: ${result['portfolio_value']:,.2f}")
            print(f"  ⏱️  Time: {result['execution_time']:.1f}s")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Generate combined portfolio
    total_value = sum(r['result']['portfolio_value'] for r in all_results)
    total_prs = sum(r['result']['processed_prs'] for r in all_results)
    
    print(f"\n🎯 Portfolio Summary:")
    print(f"  Repositories Analyzed: {len(all_results)}")
    print(f"  Total Portfolio Value: ${total_value:,.2f}")
    print(f"  Total PRs Processed: {total_prs}")
    print(f"  Average Value per PR: ${total_value/total_prs:,.2f}")
    
    return all_results

# Generate portfolio
asyncio.run(generate_complete_portfolio())
```

### 3. Custom Business Value Analysis

```python
import asyncio
from services.historical_pr_analyzer import HistoricalPRAnalyzer
from services.portfolio_validator import PortfolioValidator

async def custom_business_analysis():
    """Perform custom business value analysis with specific criteria."""
    
    analyzer = HistoricalPRAnalyzer(github_token="your_token")
    validator = PortfolioValidator()
    
    # Analyze repository
    results = await analyzer.analyze_repository_history("kubernetes/kubernetes")
    
    # Filter for specific types of contributions
    feature_prs = []
    performance_prs = []
    security_prs = []
    
    for pr in results['pr_analyses']:
        title_lower = pr['title'].lower()
        
        if any(keyword in title_lower for keyword in ['feat', 'feature', 'add', 'implement']):
            feature_prs.append(pr)
        elif any(keyword in title_lower for keyword in ['perf', 'optimize', 'performance', 'speed']):
            performance_prs.append(pr)
        elif any(keyword in title_lower for keyword in ['security', 'vuln', 'cve', 'auth']):
            security_prs.append(pr)
    
    # Calculate specialized metrics
    feature_value = sum(pr.get('business_value', 0) for pr in feature_prs)
    performance_value = sum(pr.get('business_value', 0) for pr in performance_prs)
    security_value = sum(pr.get('business_value', 0) for pr in security_prs)
    
    print(f"📊 Specialized Analysis Results:")
    print(f"  Feature Development:")
    print(f"    PRs: {len(feature_prs)}")
    print(f"    Value: ${feature_value:,.2f}")
    print(f"  Performance Optimization:")
    print(f"    PRs: {len(performance_prs)}")
    print(f"    Value: ${performance_value:,.2f}")
    print(f"  Security Improvements:")
    print(f"    PRs: {len(security_prs)}")
    print(f"    Value: ${security_value:,.2f}")
    
    # Generate specialized portfolio
    specialized_data = {
        "feature_contributions": feature_prs,
        "performance_contributions": performance_prs,
        "security_contributions": security_prs
    }
    
    # Validate and export
    portfolio = validator.validate_and_generate_portfolio(specialized_data)
    validator.export_html("specialized_portfolio.html")
    
    return portfolio

# Run custom analysis
asyncio.run(custom_business_analysis())
```

## Advanced Usage Examples

### 4. MLOps Pipeline with Custom Models

```python
import asyncio
from mlops.mlflow_registry import MLflowRegistry

async def deploy_custom_models():
    """Deploy and manage custom ML models."""
    
    registry = MLflowRegistry()
    
    # Register a new custom model
    custom_models = [
        {
            "name": "pr_impact_predictor_v3",
            "version": "3.1.0",
            "accuracy": 0.96,
            "metadata": {
                "training_data": "github_prs_2024",
                "features": ["code_changes", "review_count", "author_experience"],
                "framework": "pytorch",
                "deployment_date": "2024-01-30"
            }
        },
        {
            "name": "business_value_classifier",
            "version": "2.0.1", 
            "accuracy": 0.93,
            "metadata": {
                "categories": ["high", "medium", "low"],
                "training_size": 50000,
                "validation_accuracy": 0.94
            }
        }
    ]
    
    # Deploy models
    for model_info in custom_models:
        success = await registry.register_model(
            model_name=model_info["name"],
            model_version=model_info["version"],
            accuracy=model_info["accuracy"],
            metadata=model_info["metadata"]
        )
        
        if success:
            print(f"✅ Deployed {model_info['name']} v{model_info['version']}")
        else:
            print(f"❌ Failed to deploy {model_info['name']}")
    
    # List all models and their performance
    all_models = await registry.list_models()
    print(f"\n📋 Active Models ({len(all_models)}):")
    
    for model in all_models:
        metrics = await registry.get_model_metrics(model.name)
        print(f"  {model.name}:")
        print(f"    Version: {model.version}")
        print(f"    Accuracy: {metrics.get('accuracy', 'N/A'):.2%}")
        print(f"    Status: {model.stage}")
    
    return all_models

# Deploy custom models
asyncio.run(deploy_custom_models())
```

### 5. Intelligent LLM Routing with Cost Optimization

```python
import asyncio
from ai_pipeline.intelligent_llm_router import IntelligentLLMRouter

async def optimize_llm_costs():
    """Demonstrate intelligent LLM routing for cost optimization."""
    
    router = IntelligentLLMRouter()
    
    # Different types of queries with varying requirements
    query_scenarios = [
        {
            "query": "Write a brief summary of this PR's changes",
            "requirements": {
                "max_cost": 0.005,  # Low cost for simple task
                "min_quality": 0.7,
                "max_latency": 3.0
            },
            "expected_provider": "openai"  # Likely GPT-3.5-turbo
        },
        {
            "query": "Perform detailed code review and suggest improvements",
            "requirements": {
                "max_cost": 0.02,   # Higher cost for complex analysis
                "min_quality": 0.95,
                "max_latency": 10.0
            },
            "expected_provider": "anthropic"  # Likely Claude-3-opus
        },
        {
            "query": "Classify this commit message sentiment",
            "requirements": {
                "max_cost": 0.001,  # Very low cost for classification
                "min_quality": 0.8,
                "max_latency": 2.0
            },
            "expected_provider": "cohere"  # Efficient for classification
        }
    ]
    
    total_original_cost = 0
    total_optimized_cost = 0
    
    print("🧠 LLM Routing Optimization Results:")
    print("=" * 60)
    
    for i, scenario in enumerate(query_scenarios, 1):
        # Get routing decision
        decision = await router.route_request(
            query=scenario["query"],
            requirements=scenario["requirements"]
        )
        
        # Calculate potential savings
        baseline_cost = 0.01  # Assume default GPT-4 cost
        optimized_cost = decision.estimated_cost
        savings = (baseline_cost - optimized_cost) / baseline_cost * 100
        
        total_original_cost += baseline_cost
        total_optimized_cost += optimized_cost
        
        print(f"\nScenario {i}: {scenario['query'][:50]}...")
        print(f"  Selected Provider: {decision.selected_provider}")
        print(f"  Selected Model: {decision.selected_model}")
        print(f"  Estimated Cost: ${optimized_cost:.4f}")
        print(f"  Quality Score: {decision.quality_score:.2f}")
        print(f"  Cost Savings: {savings:.1f}%")
    
    overall_savings = (total_original_cost - total_optimized_cost) / total_original_cost * 100
    print(f"\n💰 Overall Cost Optimization:")
    print(f"  Original Cost: ${total_original_cost:.4f}")
    print(f"  Optimized Cost: ${total_optimized_cost:.4f}")
    print(f"  Total Savings: {overall_savings:.1f}%")
    
    return {
        "original_cost": total_original_cost,
        "optimized_cost": total_optimized_cost,
        "savings_percentage": overall_savings
    }

# Run cost optimization demo
asyncio.run(optimize_llm_costs())
```

### 6. Batch Processing for Large Organizations

```python
import asyncio
from pipeline.end_to_end_integration import EndToEndPipeline

async def process_organization_repositories():
    """Process all repositories for a large organization."""
    
    pipeline = EndToEndPipeline()
    
    # Example: Process all Microsoft repositories (subset)
    microsoft_repos = [
        "microsoft/TypeScript",
        "microsoft/vscode", 
        "microsoft/PowerToys",
        "microsoft/terminal",
        "microsoft/calculator",
        "microsoft/WSL2-Linux-Kernel",
        "microsoft/playwright",
        "microsoft/PowerShell"
    ]
    
    # Process in batches to respect rate limits
    batch_size = 3
    all_results = []
    
    print(f"🏢 Processing {len(microsoft_repos)} Microsoft repositories...")
    print(f"📦 Batch size: {batch_size}")
    
    for i in range(0, len(microsoft_repos), batch_size):
        batch = microsoft_repos[i:i + batch_size]
        print(f"\n📋 Processing batch {i//batch_size + 1}...")
        
        # Process batch concurrently
        batch_tasks = []
        for repo in batch:
            task = pipeline.run_complete_pipeline(repo)
            batch_tasks.append(task)
        
        # Wait for batch completion
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results
        for repo, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                print(f"  ❌ {repo}: {result}")
                all_results.append({"repo": repo, "error": str(result)})
            else:
                print(f"  ✅ {repo}: ${result['portfolio_value']:,.2f}")
                all_results.append({"repo": repo, "result": result})
        
        # Rate limiting delay between batches
        if i + batch_size < len(microsoft_repos):
            print("  ⏸️  Rate limiting pause...")
            await asyncio.sleep(60)  # 1 minute between batches
    
    # Generate organization summary
    successful_results = [r for r in all_results if 'result' in r]
    failed_results = [r for r in all_results if 'error' in r]
    
    total_value = sum(r['result']['portfolio_value'] for r in successful_results)
    total_prs = sum(r['result']['processed_prs'] for r in successful_results)
    
    print(f"\n🎯 Microsoft Organization Summary:")
    print(f"  Repositories Processed: {len(successful_results)}")
    print(f"  Repositories Failed: {len(failed_results)}")
    print(f"  Total Portfolio Value: ${total_value:,.2f}")
    print(f"  Total PRs Analyzed: {total_prs:,}")
    print(f"  Average Value per Repo: ${total_value/len(successful_results):,.2f}")
    print(f"  Average Value per PR: ${total_value/total_prs:.2f}")
    
    return {
        "successful": successful_results,
        "failed": failed_results,
        "summary": {
            "total_value": total_value,
            "total_prs": total_prs,
            "success_rate": len(successful_results) / len(all_results)
        }
    }

# Process organization repositories
asyncio.run(process_organization_repositories())
```

### 7. Real-time Monitoring and Alerting

```python
import asyncio
import time
from pipeline.end_to_end_integration import EndToEndPipeline

async def monitoring_dashboard():
    """Demonstrate real-time monitoring capabilities."""
    
    pipeline = EndToEndPipeline()
    pipeline.enable_monitoring()
    
    print("📊 Starting Real-time Monitoring Dashboard...")
    print("=" * 60)
    
    # Simulate processing activity
    test_repositories = [
        "facebook/react",
        "vuejs/vue",
        "angular/angular"
    ]
    
    # Start monitoring loop
    monitoring_duration = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < monitoring_duration:
        # Run health checks
        health = pipeline.run_health_checks()
        metrics = pipeline.get_metrics()
        
        # Display current status
        current_time = time.strftime("%H:%M:%S")
        print(f"\n[{current_time}] 📈 System Status Dashboard")
        print(f"Overall Health: {health['overall_status']}")
        print(f"Database: {health['database']['status']} ({health['database']['response_time']})")
        print(f"MLflow: {health['mlflow']['status']} ({health['mlflow']['models_available']} models)")
        print(f"LLM Router: {health['llm_router']['status']} ({health['llm_router']['providers_online']} providers)")
        
        # Performance metrics
        print(f"\n📊 Performance Metrics:")
        print(f"  Executions: {metrics['pipeline_executions_total']}")
        print(f"  Average Duration: {metrics['pipeline_duration_seconds']:.1f}s")
        print(f"  Error Count: {metrics['pipeline_errors_total']}")
        print(f"  Success Rate: {((metrics['pipeline_executions_total'] - metrics['pipeline_errors_total']) / max(metrics['pipeline_executions_total'], 1)) * 100:.1f}%")
        
        # Simulate some processing activity
        if metrics['pipeline_executions_total'] < 5:
            repo = test_repositories[metrics['pipeline_executions_total'] % len(test_repositories)]
            print(f"🔄 Processing {repo}...")
            
            # Simulate work (normally would be actual processing)
            await pipeline.process_pr_async({"number": metrics['pipeline_executions_total'] + 1})
        
        # Check for alerts
        if metrics['pipeline_errors_total'] > 0:
            print("⚠️  ALERT: Errors detected in pipeline execution!")
        
        if health['overall_status'] != 'healthy':
            print("🚨 CRITICAL: System health check failed!")
        
        # Wait before next update
        await asyncio.sleep(30)  # Update every 30 seconds
    
    print(f"\n✅ Monitoring completed. Final metrics:")
    final_metrics = pipeline.get_metrics()
    return final_metrics

# Run monitoring dashboard
asyncio.run(monitoring_dashboard())
```

### 8. Export and Integration Examples

```python
import json
from services.portfolio_validator import PortfolioValidator

def export_for_different_audiences():
    """Export portfolio data in formats for different audiences."""
    
    # Sample portfolio data
    portfolio_data = {
        "achievements": [
            {
                "title": "Microservices Architecture Implementation",
                "category": "architecture",
                "impact_score": 95,
                "business_value": 75000,
                "technical_details": "Designed and implemented microservices architecture serving 1M+ users",
                "technologies": ["Docker", "Kubernetes", "Go", "Redis"]
            },
            {
                "title": "Performance Optimization Campaign", 
                "category": "performance",
                "impact_score": 88,
                "business_value": 45000,
                "technical_details": "Reduced API response time by 60% through database optimization",
                "technologies": ["PostgreSQL", "Python", "Redis", "Prometheus"]
            }
        ]
    }
    
    validator = PortfolioValidator()
    
    # 1. Executive Summary (for management/HR)
    executive_summary = validator.generate_executive_summary(portfolio_data)
    with open("executive_summary.json", "w") as f:
        json.dump(executive_summary, f, indent=2)
    
    print("📄 Executive Summary (executive_summary.json):")
    print(f"  Total Value: ${executive_summary['total_portfolio_value']:,.2f}")
    print(f"  Key Achievements: {len(executive_summary['top_achievements'])}")
    print(f"  Business Impact: {executive_summary['business_impact_summary']}")
    
    # 2. Technical Report (for technical teams)
    technical_report = validator.generate_technical_report(portfolio_data)
    with open("technical_report.json", "w") as f:
        json.dump(technical_report, f, indent=2)
    
    print(f"\n🔧 Technical Report (technical_report.json):")
    print(f"  Methodologies: {', '.join(technical_report['methodologies_used'])}")
    print(f"  Technologies: {', '.join(technical_report['technologies_summary'])}")
    print(f"  Confidence Level: {technical_report['statistical_confidence']:.1%}")
    
    # 3. Resume Format (for job applications)
    resume_format = validator.format_for_resume(portfolio_data)
    with open("resume_achievements.txt", "w") as f:
        for achievement in resume_format['bullet_points']:
            f.write(f"• {achievement}\n")
    
    print(f"\n📝 Resume Format (resume_achievements.txt):")
    for bullet in resume_format['bullet_points'][:3]:
        print(f"  • {bullet}")
    
    # 4. LinkedIn Format (for professional networking)
    linkedin_format = validator.format_for_linkedin(portfolio_data)
    with open("linkedin_summary.md", "w") as f:
        f.write(linkedin_format['professional_summary'])
    
    print(f"\n💼 LinkedIn Format (linkedin_summary.md):")
    print(f"  Summary: {linkedin_format['professional_summary'][:100]}...")
    print(f"  Hashtags: {', '.join(linkedin_format['suggested_hashtags'])}")
    
    return {
        "executive": executive_summary,
        "technical": technical_report,
        "resume": resume_format,
        "linkedin": linkedin_format
    }

# Generate exports for different audiences
export_for_different_audiences()
```

## Performance Testing Examples

### 9. Load Testing and Benchmarking

```python
import asyncio
import time
import statistics
from pipeline.end_to_end_integration import EndToEndPipeline

async def performance_benchmark():
    """Benchmark system performance under different loads."""
    
    pipeline = EndToEndPipeline()
    
    # Test scenarios
    scenarios = [
        {"name": "Small Repo", "pr_count": 10, "concurrent": 1},
        {"name": "Medium Repo", "pr_count": 50, "concurrent": 3},
        {"name": "Large Repo", "pr_count": 200, "concurrent": 5},
        {"name": "Enterprise Load", "pr_count": 1000, "concurrent": 10}
    ]
    
    results = []
    
    print("⚡ Performance Benchmark Results:")
    print("=" * 60)
    
    for scenario in scenarios:
        print(f"\n🧪 Testing {scenario['name']}...")
        
        # Generate test data
        test_prs = []
        for i in range(scenario['pr_count']):
            test_prs.append({
                "number": i + 1,
                "title": f"Test PR {i + 1}",
                "additions": 100 + (i * 10),
                "deletions": 50 + (i * 5)
            })
        
        # Run benchmark
        start_time = time.time()
        
        if scenario['concurrent'] == 1:
            # Sequential processing
            for pr in test_prs:
                await pipeline.process_pr_async(pr)
        else:
            # Concurrent processing
            batch_results = await pipeline.process_batch_async(
                test_prs, 
                batch_size=scenario['concurrent']
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate metrics
        prs_per_second = scenario['pr_count'] / duration
        avg_time_per_pr = duration / scenario['pr_count']
        
        scenario_result = {
            "scenario": scenario['name'],
            "pr_count": scenario['pr_count'],
            "concurrent": scenario['concurrent'],
            "total_time": duration,
            "prs_per_second": prs_per_second,
            "avg_time_per_pr": avg_time_per_pr
        }
        
        results.append(scenario_result)
        
        print(f"  Total Time: {duration:.2f}s")
        print(f"  PRs/Second: {prs_per_second:.2f}")
        print(f"  Avg Time/PR: {avg_time_per_pr:.3f}s")
        
        # Performance assertion
        if scenario['name'] == "Small Repo":
            assert duration < 30, f"Small repo should complete in <30s, took {duration:.2f}s"
        elif scenario['name'] == "Medium Repo":
            assert duration < 120, f"Medium repo should complete in <2min, took {duration:.2f}s"
        elif scenario['name'] == "Large Repo":
            assert duration < 300, f"Large repo should complete in <5min, took {duration:.2f}s"
    
    # Summary statistics
    total_prs = sum(r['pr_count'] for r in results)
    total_time = sum(r['total_time'] for r in results)
    avg_throughput = statistics.mean([r['prs_per_second'] for r in results])
    
    print(f"\n📊 Benchmark Summary:")
    print(f"  Total PRs Processed: {total_prs:,}")
    print(f"  Total Processing Time: {total_time:.2f}s")
    print(f"  Average Throughput: {avg_throughput:.2f} PRs/second")
    print(f"  Peak Throughput: {max(r['prs_per_second'] for r in results):.2f} PRs/second")
    
    return results

# Run performance benchmark
asyncio.run(performance_benchmark())
```

These examples demonstrate the comprehensive capabilities of the Achievement Collector System, from basic repository analysis to enterprise-scale deployment and monitoring. Each example is production-ready and demonstrates best practices for AI/MLOps engineering.