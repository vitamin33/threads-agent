# Fixed stats endpoint for achievement collector
# This handles the business_value as text column issue

from sqlalchemy import func, cast, Float
from sqlalchemy.orm import Session
import json
import re


def calculate_business_value_sum(achievements):
    """Extract and sum business values from text/JSON field"""
    total_value = 0.0
    
    for achievement in achievements:
        if achievement.business_value:
            try:
                # Handle different formats
                value_str = achievement.business_value
                
                # If it's a number string
                if isinstance(value_str, str):
                    # Remove currency symbols and commas
                    cleaned = re.sub(r'[^\d.-]', '', value_str)
                    if cleaned:
                        total_value += float(cleaned)
                        
                # If it's JSON
                elif value_str.startswith('{'):
                    data = json.loads(value_str)
                    if 'total_value' in data:
                        total_value += float(data['total_value'])
                    elif 'value' in data:
                        total_value += float(data['value'])
                        
            except (ValueError, json.JSONDecodeError):
                # Skip invalid values
                continue
                
    return total_value


def get_achievement_stats_fixed(db: Session):
    """Fixed version of get_achievement_stats that handles text business_value"""
    
    # Get basic stats (without business_value sum)
    stats = db.query(
        func.count(AchievementModel.id).label("total_achievements"),
        func.sum(AchievementModel.time_saved_hours).label("total_time_saved"),
        func.avg(AchievementModel.impact_score).label("avg_impact_score"),
        func.avg(AchievementModel.complexity_score).label("avg_complexity_score"),
    ).first()
    
    # Get all achievements to calculate business value sum
    all_achievements = db.query(AchievementModel).all()
    total_business_value = calculate_business_value_sum(all_achievements)
    
    # Get category stats
    category_stats = (
        db.query(
            AchievementModel.category,
            func.count(AchievementModel.id).label("count"),
        )
        .group_by(AchievementModel.category)
        .all()
    )
    
    return {
        "total_achievements": stats.total_achievements or 0,
        "total_value_generated": total_business_value,
        "total_time_saved_hours": float(stats.total_time_saved or 0),
        "average_impact_score": float(stats.avg_impact_score or 0),
        "average_complexity_score": float(stats.avg_complexity_score or 0),
        "by_category": {cat: count for cat, count in category_stats},
    }