'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { AchievementsLive } from './achievements-live';

// Fetcher for SWR
const fetcher = (url: string) => fetch(url).then(res => res.json());

interface AchievementsLiveAPIProps {
  showHeroStats?: boolean;
  showFilters?: boolean;
  limit?: number;
  featuredOnly?: boolean;
  fallbackToStatic?: boolean;
}

export function AchievementsLiveAPI({
  showHeroStats = true,
  showFilters = true,
  limit = 6,
  featuredOnly = false,
  fallbackToStatic = true,
}: AchievementsLiveAPIProps) {
  const [useStatic, setUseStatic] = useState(fallbackToStatic);

  // Try to fetch from your real Achievement Collector API
  const {
    data: liveData,
    error,
    isLoading,
  } = useSWR(
    useStatic
      ? null
      : `${process.env.NEXT_PUBLIC_ACHIEVEMENT_API_URL}/api/v1/portfolio/achievements`,
    fetcher,
    {
      refreshInterval: 300000, // 5 minutes
      revalidateOnFocus: false,
      onError: () => {
        console.log('Live API failed, falling back to static data');
        setUseStatic(true);
      },
    }
  );

  // Loading state
  if (isLoading && !useStatic) {
    return (
      <div className="space-y-4">
        <div className="text-center">
          <div className="animate-pulse flex items-center justify-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-ping" />
            <span className="text-sm text-muted-foreground">
              Loading live data...
            </span>
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-64 bg-muted/50 rounded-lg animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  // Error state - fallback to static
  if (error || useStatic) {
    return (
      <>
        {!useStatic && (
          <div className="mb-4 p-3 rounded-lg bg-yellow-50 border border-yellow-200">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">Live API unavailable.</span> Showing
              static portfolio data.
            </p>
          </div>
        )}
        <AchievementsLive
          showHeroStats={showHeroStats}
          showFilters={showFilters}
          limit={limit}
          featuredOnly={featuredOnly}
        />
      </>
    );
  }

  // Live data available
  return (
    <>
      <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <p className="text-sm text-green-800">
            <span className="font-medium">Live data active.</span> Last updated:{' '}
            {new Date(liveData.meta.generated_at).toLocaleString()}
          </p>
        </div>
      </div>
      <AchievementsLive
        showHeroStats={showHeroStats}
        showFilters={showFilters}
        limit={limit}
        featuredOnly={featuredOnly}
      />
    </>
  );
}
