"""
CSV export functionality for achievements.
"""

import csv
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..base import BaseExporter


class CSVExporter(BaseExporter):
    """Export achievements as CSV for spreadsheet analysis."""
    
    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        format_type: str = "detailed"
    ) -> str:
        """
        Export achievements as CSV.
        
        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            format_type: "detailed" or "summary"
            
        Returns:
            CSV string
        """
        achievements = self.get_achievements(db, user_id, filters)
        
        if format_type == "detailed":
            return self._export_detailed(achievements)
        else:
            return self._export_summary(achievements)
    
    def _export_detailed(self, achievements: List) -> str:
        """Export detailed achievement data."""
        output = StringIO()
        
        fieldnames = [
            'id', 'title', 'description', 'category', 'impact_score',
            'complexity_score', 'skills', 'tags', 'business_value',
            'duration_hours', 'started_at', 'completed_at',
            'portfolio_ready', 'source_type', 'source_id'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for achievement in achievements:
            writer.writerow({
                'id': achievement.id,
                'title': achievement.title,
                'description': achievement.description or '',
                'category': achievement.category,
                'impact_score': achievement.impact_score or 0,
                'complexity_score': achievement.complexity_score or 0,
                'skills': '; '.join(achievement.skills_demonstrated or []),
                'tags': '; '.join(achievement.tags or []),
                'business_value': achievement.business_value or '',
                'duration_hours': achievement.duration_hours or 0,
                'started_at': achievement.started_at.strftime('%Y-%m-%d') if achievement.started_at else '',
                'completed_at': achievement.completed_at.strftime('%Y-%m-%d') if achievement.completed_at else '',
                'portfolio_ready': 'Yes' if achievement.portfolio_ready else 'No',
                'source_type': achievement.source_type,
                'source_id': achievement.source_id or ''
            })
        
        return output.getvalue()
    
    def _export_summary(self, achievements: List) -> str:
        """Export summary achievement data."""
        output = StringIO()
        
        # Group by category
        category_stats = {}
        for achievement in achievements:
            if achievement.category not in category_stats:
                category_stats[achievement.category] = {
                    'count': 0,
                    'total_impact': 0,
                    'avg_complexity': 0,
                    'total_hours': 0,
                    'skills': set()
                }
            
            stats = category_stats[achievement.category]
            stats['count'] += 1
            stats['total_impact'] += achievement.impact_score or 0
            stats['avg_complexity'] += achievement.complexity_score or 0
            stats['total_hours'] += achievement.duration_hours or 0
            
            if achievement.skills_demonstrated:
                stats['skills'].update(achievement.skills_demonstrated)
        
        # Calculate averages
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                stats['avg_complexity'] = stats['avg_complexity'] / stats['count']
        
        # Write summary
        fieldnames = [
            'category', 'achievement_count', 'total_impact_score',
            'avg_complexity_score', 'total_hours', 'unique_skills'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for category, stats in sorted(category_stats.items()):
            writer.writerow({
                'category': category,
                'achievement_count': stats['count'],
                'total_impact_score': stats['total_impact'],
                'avg_complexity_score': round(stats['avg_complexity'], 2),
                'total_hours': stats['total_hours'],
                'unique_skills': len(stats['skills'])
            })
        
        # Add totals row
        writer.writerow({
            'category': 'TOTAL',
            'achievement_count': len(achievements),
            'total_impact_score': sum(a.impact_score or 0 for a in achievements),
            'avg_complexity_score': round(
                sum(a.complexity_score or 0 for a in achievements) / len(achievements), 2
            ) if achievements else 0,
            'total_hours': sum(a.duration_hours or 0 for a in achievements),
            'unique_skills': len(set(
                skill for a in achievements 
                if a.skills_demonstrated 
                for skill in a.skills_demonstrated
            ))
        })
        
        return output.getvalue()
    
    def export_to_file(self, csv_data: str, filename: str) -> str:
        """
        Export CSV data to file.
        
        Args:
            csv_data: CSV string data
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        with open(filename, 'w', newline='') as f:
            f.write(csv_data)
            
        return filename