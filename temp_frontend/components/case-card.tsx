import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CaseCardProps {
  title: string;
  summary: string;
  techStack: string[];
  outcomes: string[];
  link: string;
  coverImage?: string;
  isExternal?: boolean;
}

export function CaseCard({
  title,
  summary,
  techStack,
  outcomes,
  link,
  coverImage,
  isExternal = false,
}: CaseCardProps) {
  return (
    <Card className="group h-full overflow-hidden transition-all duration-300 hover:shadow-lg">
      {/* Cover Image or Placeholder */}
      <div className="relative h-48 overflow-hidden bg-gradient-to-br from-primary/10 to-secondary/10">
        {coverImage ? (
          <Image
            src={coverImage}
            alt={title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mx-auto h-16 w-16 rounded-lg bg-primary/20 flex items-center justify-center mb-2">
                <svg
                  className="h-8 w-8 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </div>
              <span className="text-xs text-muted-foreground">Case Study</span>
            </div>
          </div>
        )}
      </div>

      <CardHeader className="pb-3">
        <CardTitle className="line-clamp-2">{title}</CardTitle>
        <p className="text-sm text-muted-foreground line-clamp-3">{summary}</p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Tech Stack */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Tech Stack
          </h4>
          <div className="flex flex-wrap gap-1">
            {techStack.map((tech, index) => (
              <span
                key={index}
                className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Outcomes */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Key Outcomes
          </h4>
          <ul className="space-y-1">
            {outcomes.slice(0, 3).map((outcome, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0"></div>
                <span className="line-clamp-1">{outcome}</span>
              </li>
            ))}
            {outcomes.length > 3 && (
              <li className="text-xs text-muted-foreground">
                +{outcomes.length - 3} more outcomes
              </li>
            )}
          </ul>
        </div>

        {/* CTA */}
        <div className="pt-2">
          <Button variant="outline" size="sm" className="w-full" asChild>
            <a
              href={link}
              target={isExternal ? '_blank' : undefined}
              rel={isExternal ? 'noopener noreferrer' : undefined}
              className="flex items-center gap-2"
            >
              <span>View Details</span>
              {isExternal && (
                <svg
                  className="h-3 w-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              )}
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
