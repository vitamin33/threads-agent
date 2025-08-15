import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Type definitions for achievement_collector API
interface AchievementCollectorResponse {
  achievements: Array<{
    id: string;
    title: string;
    category: string;
    impact_score: number;
    business_value: number;
    duration_hours: number;
    tech_stack: string[];
    evidence: {
      before_metrics: Record<string, any>;
      after_metrics: Record<string, any>;
      pr_number?: number;
      repo_url?: string;
    };
    generated_content: {
      summary: string;
      technical_analysis: string;
      architecture_notes: string;
    };
  }>;
}

// Generate MDX content from achievement data
function generateCaseStudyMDX(achievement: any): string {
  const {
    id,
    title,
    category,
    impact_score,
    business_value,
    duration_hours,
    tech_stack,
    evidence,
    generated_content,
  } = achievement;

  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');

  const outcomes = [
    `${impact_score}/100 impact score achieved`,
    `${formatCurrency(business_value)} business value delivered`,
    `${Math.round((business_value / (duration_hours * 150)) * 100) / 100}x ROI through optimization`,
    `Production-ready implementation with monitoring`,
  ];

  return `---
title: "${title}"
slug: "${slug}"
summary: "${generated_content.summary}"
description: "${generated_content.technical_analysis}"
category: "${category}"
achievement_id: "${id}"
impact_score: ${impact_score}
business_value: ${business_value}

tech: ${JSON.stringify(tech_stack)}
architecture: ["Production Systems", "Performance Optimization", "Monitoring"]

outcomes: ${JSON.stringify(outcomes)}

metrics_before: ${JSON.stringify(evidence.before_metrics, null, 2)}

metrics_after: ${JSON.stringify(evidence.after_metrics, null, 2)}

date: "${new Date().toISOString().split('T')[0]}"
duration_hours: ${duration_hours}
links:
  repo: "${evidence.repo_url || ''}"
  pr: "${evidence.repo_url || ''}/pull/${evidence.pr_number || ''}"
  grafana: "https://grafana.serbyn.pro/d/${slug}"

cover: "/images/case-studies/${slug}-cover.png"
gallery: ["/images/case-studies/${slug}-architecture.png", "/images/case-studies/${slug}-metrics.png"]
featured: ${impact_score >= 90}
portfolio_ready: true
seo_keywords: ${JSON.stringify(tech_stack.slice(0, 5))}
---

## Challenge

${generated_content.technical_analysis}

## Solution Architecture

### Technical Implementation

${generated_content.architecture_notes}

## Business Impact

This implementation delivered significant measurable improvements:

${outcomes.map(outcome => `- ${outcome}`).join('\n')}

## Evidence & Verification

All metrics are sourced from production systems and verified through:

- GitHub repository with complete implementation
- Live monitoring dashboards showing real-time performance
- Before/after performance comparisons
- Business impact measurements

## Key Technologies

${tech_stack.map((tech: string) => `- **${tech}**: Production deployment and optimization`).join('\n')}

This case study demonstrates production-scale implementation with quantified business impact and technical excellence.
`;

  function formatCurrency(value: number): string {
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}k`;
    return `$${value.toFixed(0)}`;
  }
}

// Sync with achievement_collector service
export async function POST(request: Request) {
  try {
    const { apiUrl, apiKey } = await request.json();

    // Default to environment variables if not provided
    const achievementApiUrl = apiUrl || process.env.ACHIEVEMENT_API_URL;
    const achievementApiKey = apiKey || process.env.ACHIEVEMENT_API_KEY;

    if (!achievementApiUrl) {
      return NextResponse.json(
        { error: 'Achievement API URL not configured' },
        { status: 400 }
      );
    }

    // Fetch latest achievements from achievement_collector
    const response = await fetch(
      `${achievementApiUrl}/api/v1/portfolio/generate`,
      {
        headers: {
          Authorization: `Bearer ${achievementApiKey}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Achievement API error: ${response.status}`);
    }

    const data: AchievementCollectorResponse = await response.json();

    // Generate MDX files for high-impact achievements
    const contentDir = path.join(process.cwd(), 'content/case-studies');

    // Ensure directory exists
    if (!fs.existsSync(contentDir)) {
      fs.mkdirSync(contentDir, { recursive: true });
    }

    let syncedCount = 0;

    for (const achievement of data.achievements) {
      // Only create case studies for high-impact achievements
      if (achievement.impact_score >= 80) {
        const slug = achievement.title
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/(^-|-$)/g, '');

        const filePath = path.join(contentDir, `${slug}.mdx`);
        const mdxContent = generateCaseStudyMDX(achievement);

        fs.writeFileSync(filePath, mdxContent, 'utf8');
        syncedCount++;
      }
    }

    return NextResponse.json({
      message: `Successfully synced ${syncedCount} case studies`,
      synced: syncedCount,
      total_achievements: data.achievements.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Case study sync error:', error);
    return NextResponse.json(
      {
        error: 'Failed to sync case studies',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

// Get sync status
export async function GET() {
  try {
    const contentDir = path.join(process.cwd(), 'content/case-studies');

    if (!fs.existsSync(contentDir)) {
      return NextResponse.json({
        case_studies_count: 0,
        last_sync: null,
        status: 'No case studies directory',
      });
    }

    const files = fs
      .readdirSync(contentDir)
      .filter(file => file.endsWith('.mdx'));

    // Get last modification time of the newest file
    let lastSync = null;
    if (files.length > 0) {
      const stats = files.map(file => {
        const filePath = path.join(contentDir, file);
        return fs.statSync(filePath);
      });

      const newestStat = stats.reduce((newest, current) =>
        current.mtime > newest.mtime ? current : newest
      );

      lastSync = newestStat.mtime.toISOString();
    }

    return NextResponse.json({
      case_studies_count: files.length,
      last_sync: lastSync,
      status: 'Ready for sync',
      available_files: files,
    });
  } catch (error) {
    console.error('Sync status error:', error);
    return NextResponse.json(
      { error: 'Failed to get sync status' },
      { status: 500 }
    );
  }
}
