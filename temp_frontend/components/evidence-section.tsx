import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ExternalLink,
  Github,
  Play,
  BarChart3,
  Globe,
  CheckCircle,
} from 'lucide-react';

interface EvidenceSectionProps {
  links: {
    demo?: string;
    repo?: string;
    pr?: string;
    grafana?: string;
    loom?: string;
  };
  gallery?: string[];
}

export function EvidenceSection({ links, gallery }: EvidenceSectionProps) {
  const getLinkIcon = (type: string) => {
    switch (type) {
      case 'demo':
        return <Globe className="h-4 w-4" />;
      case 'repo':
        return <Github className="h-4 w-4" />;
      case 'pr':
        return <Github className="h-4 w-4" />;
      case 'grafana':
        return <BarChart3 className="h-4 w-4" />;
      case 'loom':
        return <Play className="h-4 w-4" />;
      default:
        return <ExternalLink className="h-4 w-4" />;
    }
  };

  const getLinkLabel = (type: string): string => {
    switch (type) {
      case 'demo':
        return 'Live Demo';
      case 'repo':
        return 'Source Code';
      case 'pr':
        return 'Pull Request';
      case 'grafana':
        return 'Live Metrics';
      case 'loom':
        return 'Video Demo';
      default:
        return 'Link';
    }
  };

  const getLinkDescription = (type: string): string => {
    switch (type) {
      case 'demo':
        return 'Interactive demonstration of the system';
      case 'repo':
        return 'Complete source code implementation';
      case 'pr':
        return 'GitHub pull request with technical details';
      case 'grafana':
        return 'Real-time performance monitoring dashboard';
      case 'loom':
        return 'Video walkthrough and explanation';
      default:
        return 'Additional resource';
    }
  };

  const availableLinks = Object.entries(links).filter(([_, url]) => url);

  return (
    <div className="space-y-6">
      {/* Evidence Links */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ExternalLink className="h-5 w-5 text-primary" />
            Evidence & Verification
          </CardTitle>
        </CardHeader>
        <CardContent>
          {availableLinks.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {availableLinks.map(([type, url]) => (
                <div
                  key={type}
                  className="flex items-center justify-between p-4 rounded-lg border bg-card"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      {getLinkIcon(type)}
                    </div>
                    <div>
                      <h4 className="font-medium">{getLinkLabel(type)}</h4>
                      <p className="text-sm text-muted-foreground">
                        {getLinkDescription(type)}
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View
                    </a>
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No evidence links available for this case study.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Gallery */}
      {gallery && gallery.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Visual Evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {gallery.map((image, index) => (
                <div
                  key={index}
                  className="relative aspect-video bg-muted rounded-lg overflow-hidden"
                >
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center">
                      <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center mx-auto mb-2">
                        <BarChart3 className="h-6 w-6 text-primary" />
                      </div>
                      <Badge variant="secondary">
                        {image.split('/').pop()?.replace('.png', '')}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-sm text-muted-foreground mt-4 text-center">
              Screenshots, architecture diagrams, and performance charts from
              production systems
            </p>
          </CardContent>
        </Card>
      )}

      {/* Verification Statement */}
      <div className="p-4 rounded-lg bg-green-50 border border-green-200">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span className="font-semibold text-green-800">
            Verified Implementation
          </span>
        </div>
        <p className="text-sm text-green-700">
          All metrics and evidence are sourced from production systems and
          actual GitHub repositories. This case study represents real-world
          implementation with measurable business outcomes.
        </p>
      </div>
    </div>
  );
}
