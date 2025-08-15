import { Button } from '@/components/ui/button';
import { BookConsultationButton } from '@/components/calendly-widget';

export function Hero() {
  return (
    <section className="relative py-24 sm:py-32 lg:py-40">
      <div className="container">
        <div className="mx-auto max-w-4xl text-center">
          {/* Main Headline */}
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            <span className="text-balance">
              AI engineer who builds reliable{' '}
              <span className="text-primary">LLM platforms</span>
            </span>
          </h1>

          {/* Subhead */}
          <p className="mx-auto mt-6 max-w-3xl text-lg sm:text-xl text-muted-foreground leading-8">
            <span className="text-pretty">
              I design and run production-ready LLM services with clear SLOs,
              MLflow registries, and cost controls. 12+ years of production
              discipline applied to AI platforms.
            </span>
          </p>

          {/* Trust Line */}
          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500"></span>
              Easelect LTD
            </span>
            <span className="text-border">·</span>
            <span>12+ years production systems</span>
            <span className="text-border">·</span>
            <span>Personal R&D lab</span>
          </div>

          {/* CTAs */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <BookConsultationButton size="lg" />

            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto min-w-[160px]"
              asChild
            >
              <a href="#proof" className="font-semibold">
                See Proof Pack
              </a>
            </Button>
          </div>

          {/* Background Elements */}
          <div className="absolute inset-0 -z-10 overflow-hidden">
            <div className="absolute left-[50%] top-[50%] h-[600px] w-[600px] -translate-x-[50%] -translate-y-[50%] rounded-full bg-gradient-to-r from-primary/20 to-secondary/20 opacity-20 blur-3xl"></div>
            <div className="absolute left-[20%] top-[20%] h-[300px] w-[300px] rounded-full bg-gradient-to-r from-accent/10 to-primary/10 opacity-30 blur-2xl"></div>
            <div className="absolute right-[20%] bottom-[20%] h-[400px] w-[400px] rounded-full bg-gradient-to-r from-secondary/10 to-accent/10 opacity-25 blur-2xl"></div>
          </div>
        </div>
      </div>
    </section>
  );
}
