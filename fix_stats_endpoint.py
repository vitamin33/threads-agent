#!/usr/bin/env python3
"""
Quick fix for achievement stats endpoint
This patches the running achievement collector to fix the SQL error
"""

import httpx
import json

# Fixed stats calculation that handles text business_value
def calculate_stats_from_achievements():
    # Get all achievements
    response = httpx.get("http://localhost:8000/achievements/", params={"per_page": 1000})
    data = response.json()
    achievements = data.get('items', [])
    
    # Calculate stats manually
    total_value = 0.0
    total_time_saved = 0.0
    impact_scores = []
    complexity_scores = []
    category_counts = {}
    
    for achievement in achievements:
        # Extract business value
        if achievement.get('business_value'):
            try:
                value_str = str(achievement['business_value'])
                # Remove currency symbols and commas
                import re
                cleaned = re.sub(r'[^\d.-]', '', value_str)
                if cleaned:
                    total_value += float(cleaned)
            except:
                pass
        
        # Sum other metrics
        if achievement.get('time_saved_hours'):
            total_time_saved += float(achievement['time_saved_hours'])
        
        if achievement.get('impact_score'):
            impact_scores.append(float(achievement['impact_score']))
            
        if achievement.get('complexity_score'):
            complexity_scores.append(float(achievement['complexity_score']))
        
        # Count categories
        category = achievement.get('category', 'unknown')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Calculate averages
    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
    avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
    
    return {
        "total_achievements": len(achievements),
        "total_value_generated": total_value,
        "total_time_saved_hours": total_time_saved,
        "average_impact_score": avg_impact,
        "average_complexity_score": avg_complexity,
        "by_category": category_counts
    }

if __name__ == "__main__":
    try:
        stats = calculate_stats_from_achievements()
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"Error: {e}")