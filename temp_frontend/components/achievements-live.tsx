'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ExternalLink,
  TrendingUp,
  Clock,
  DollarSign,
  Target,
} from 'lucide-react';
import achievementsData from '@/data/achievements.json';

// TypeScript interfaces
interface Evidence {
  pr_number?: number;
  commits?: number;
  files_changed?: number;
  additions?: number;
  deletions?: number;
  before_metrics: Record<string, any>;
  after_metrics: Record<string, any>;
}

interface Achievement {
  id: string;
  date: string;
  title: string;
  category: string;
  tags: string[];
  skills: string[];
  impact_score: number;
  complexity_score: number;
  business_value: number;
  time_saved_hours: number;
  duration_hours: number;
  performance_improvement: number;
  description: string;
  summary: string;
  technical_details: string;
  evidence: Evidence;
  link: string;
  source_type: string;
  featured: boolean;
  portfolio_ready: boolean;
}

interface AchievementsMeta {
  generated_at: string;
  total_achievements: number;
  total_business_value: number;
  total_time_saved_hours: number;
  avg_impact_score: number;
}

interface AchievementsData {
  meta: AchievementsMeta;
  achievements: Achievement[];
}

// Get impact score color
const getImpactScoreColor = (score: number): string => {
  if (score >= 90) return 'bg-green-600';
  if (score >= 80) return 'bg-blue-600';
  if (score >= 70) return 'bg-yellow-600';
  return 'bg-gray-600';
};

// Format currency
const formatCurrency = (value: number): string => {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value.toFixed(0)}`;
};

// Format percentage improvement
const formatPercentage = (value: number): string => {
  return `+${value.toFixed(0)}%`;
};

// Achievement Card Component
interface AchievementCardProps {
  achievement: Achievement;
}

function AchievementCard({ achievement }: AchievementCardProps) {
  const impactColor = getImpactScoreColor(achievement.impact_score);

  return (
    <Card className="h-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold leading-tight mb-2">
              {achievement.title}
            </CardTitle>
            <div className="flex items-center gap-2 mb-2">
              <Badge
                className={`${impactColor} text-white text-xs font-medium`}
              >
                Impact: {achievement.impact_score}/100
              </Badge>
              <span className="text-xs text-muted-foreground">
                {new Date(achievement.date).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          {achievement.business_value > 0 && (
            <div className="flex items-center gap-1 text-sm">
              <DollarSign className="h-3 w-3 text-green-600" />
              <span className="font-medium text-green-600">
                {formatCurrency(achievement.business_value)}
              </span>
            </div>
          )}

          {achievement.performance_improvement > 0 && (
            <div className="flex items-center gap-1 text-sm">
              <TrendingUp className="h-3 w-3 text-blue-600" />
              <span className="font-medium text-blue-600">
                {formatPercentage(achievement.performance_improvement)}
              </span>
            </div>
          )}

          {achievement.time_saved_hours > 0 && (
            <div className="flex items-center gap-1 text-sm">
              <Clock className="h-3 w-3 text-purple-600" />
              <span className="font-medium text-purple-600">
                {achievement.time_saved_hours}h saved
              </span>
            </div>
          )}

          <div className="flex items-center gap-1 text-sm">
            <Target className="h-3 w-3 text-orange-600" />
            <span className="font-medium text-orange-600">
              {achievement.duration_hours}h work
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
          {achievement.summary}
        </p>

        {/* Before/After Metrics */}
        {achievement.evidence && (
          <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-muted/50 rounded-lg">
            <div>
              <h5 className="text-xs font-medium text-muted-foreground mb-1">
                Before
              </h5>
              <div className="space-y-1">
                {Object.entries(achievement.evidence.before_metrics)
                  .slice(0, 2)
                  .map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="text-muted-foreground">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="ml-1 font-medium">{String(value)}</span>
                    </div>
                  ))}
              </div>
            </div>
            <div>
              <h5 className="text-xs font-medium text-muted-foreground mb-1">
                After
              </h5>
              <div className="space-y-1">
                {Object.entries(achievement.evidence.after_metrics)
                  .slice(0, 2)
                  .map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="text-muted-foreground">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="ml-1 font-medium text-green-600">
                        {String(value)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-4">
          {achievement.tags.slice(0, 3).map(tag => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {achievement.tags.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{achievement.tags.length - 3}
            </Badge>
          )}
        </div>

        {/* Evidence Link */}
        {achievement.link && (
          <Button variant="outline" size="sm" className="w-full" asChild>
            <a
              href={achievement.link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              <ExternalLink className="h-3 w-3" />
              View Evidence{' '}
              {achievement.evidence.pr_number &&
                `(PR #${achievement.evidence.pr_number})`}
            </a>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// Main Achievements Component
interface AchievementsLiveProps {
  showHeroStats?: boolean;
  showFilters?: boolean;
  limit?: number;
  featuredOnly?: boolean;
}

export function AchievementsLive({
  showHeroStats = true,
  showFilters = true,
  limit = 6,
  featuredOnly = false,
}: AchievementsLiveProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');

  const data: AchievementsData = achievementsData;

  // Get unique categories and tags
  const categories = useMemo(() => {
    const cats = Array.from(new Set(data.achievements.map(a => a.category)));
    return ['all', ...cats];
  }, [data.achievements]);

  const tags = useMemo(() => {
    const allTags = data.achievements.flatMap(a => a.tags);
    const uniqueTags = Array.from(new Set(allTags));
    return ['all', ...uniqueTags.sort()];
  }, [data.achievements]);

  // Filter achievements
  const filteredAchievements = useMemo(() => {
    let filtered = data.achievements;

    if (featuredOnly) {
      filtered = filtered.filter(a => a.featured);
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(a => a.category === selectedCategory);
    }

    if (selectedTag !== 'all') {
      filtered = filtered.filter(a => a.tags.includes(selectedTag));
    }

    return filtered.slice(0, limit);
  }, [data.achievements, selectedCategory, selectedTag, limit, featuredOnly]);

  return (
    <div className="space-y-8">
      {/* Hero Stats */}
      {showHeroStats && (
        <div className="text-center mb-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-lg bg-muted/50">
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(data.meta.total_business_value)}
              </div>
              <div className="text-sm text-muted-foreground">Total Value</div>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <div className="text-2xl font-bold text-blue-600">
                {data.meta.avg_impact_score}/100
              </div>
              <div className="text-sm text-muted-foreground">Avg Impact</div>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <div className="text-2xl font-bold text-purple-600">
                {data.meta.total_time_saved_hours}h
              </div>
              <div className="text-sm text-muted-foreground">Time Saved</div>
            </div>
            <div className="p-4 rounded-lg bg-muted/50">
              <div className="text-2xl font-bold text-orange-600">
                {data.meta.total_achievements}
              </div>
              <div className="text-sm text-muted-foreground">Achievements</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="space-y-4">
          {/* Category Filter */}
          <div>
            <h4 className="text-sm font-medium mb-2">Category</h4>
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <Button
                  key={category}
                  variant={
                    selectedCategory === category ? 'default' : 'outline'
                  }
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                  className="capitalize"
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>

          {/* Tag Filter */}
          <div>
            <h4 className="text-sm font-medium mb-2">Technology</h4>
            <div className="flex flex-wrap gap-2">
              {tags.slice(0, 8).map(tag => (
                <Button
                  key={tag}
                  variant={selectedTag === tag ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedTag(tag)}
                >
                  {tag}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Achievements Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredAchievements.map(achievement => (
          <AchievementCard key={achievement.id} achievement={achievement} />
        ))}
      </div>

      {/* No Results */}
      {filteredAchievements.length === 0 && (
        <div className="text-center py-8">
          <p className="text-muted-foreground">
            No achievements found for the selected filters.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSelectedCategory('all');
              setSelectedTag('all');
            }}
            className="mt-2"
          >
            Clear Filters
          </Button>
        </div>
      )}
    </div>
  );
}
