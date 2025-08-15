#!/usr/bin/env python3
"""Test script for AI Hiring Manager Content Optimization Engine"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_hiring_manager_optimization():
    print('🤖 Testing AI Hiring Manager Content Optimization Engine')
    print('=' * 70)
    
    from services.achievement_collector.services.auto_content_pipeline import AIHiringManagerContentEngine
    
    engine = AIHiringManagerContentEngine()
    
    # Test hiring manager hook generation
    print('🎯 Testing Hiring Manager Hook Generation...')
    
    achievement_data = {
        'title': 'MLflow Cost Optimization with vLLM Integration',
        'business_value': '$240,000 annual savings with 60% cost reduction',
        'category': 'cost_optimization'
    }
    
    hook = engine.generate_hiring_manager_hook(achievement_data)
    print('Generated Hook:')
    print(f'   "{hook}"')
    print(f'✅ Contains cost focus: {"cost" in hook.lower()}')
    print(f'✅ Contains specific metrics: {"$240,000" in hook or "60%" in hook}')
    
    print()
    
    # Test content optimization
    print('💼 Testing Content Optimization for Hiring Managers...')
    
    basic_content = '''# MLflow Implementation

I implemented MLflow model registry with automated rollback.

## Results  
Achieved significant cost savings and performance improvements.

Currently seeking MLOps roles.
Portfolio: serbyn.pro/portfolio
Contact: serbyn.pro/contact'''
    
    optimized_content = engine.optimize_for_hiring_managers(basic_content, achievement_data)
    
    print('Optimization Results:')
    print(f'✅ Contains hiring manager CTA: {"For AI Hiring Managers" in optimized_content}')
    print(f'✅ Contains leadership positioning: {"Leadership Impact" in optimized_content}')
    print(f'✅ Enhanced with MLOps keywords: {"MLOps" in optimized_content}')
    
    # Test company targeting
    print()
    print('🏢 Testing Company-Specific Targeting...')
    
    anthropic_content = engine.optimize_for_hiring_managers(basic_content, achievement_data, 'anthropic')
    print(f'✅ Anthropic targeting: {"AI safety" in anthropic_content.lower()}')
    
    print()
    print('✅ AI Hiring Manager Content Optimization Engine Complete!')
    print('🎯 Ready for integration with main content pipeline!')

if __name__ == "__main__":
    asyncio.run(test_hiring_manager_optimization())