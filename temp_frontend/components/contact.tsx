import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  BookConsultationButton,
  ScheduleCallButton,
} from '@/components/calendly-widget';

export function Contact() {
  return (
    <section id="contact" className="py-16 sm:py-24 bg-muted/30">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
              Ready to optimize your LLM infrastructure?
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Book a 30-minute discovery call to discuss your project
              requirements and explore how we can reduce costs while improving
              reliability.
            </p>
          </div>

          {/* Contact Options */}
          <div className="grid gap-8 lg:grid-cols-2">
            {/* Primary CTA - Calendly */}
            <Card className="relative overflow-hidden">
              <CardContent className="p-8 text-center">
                <div className="mb-6">
                  <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <svg
                      className="w-8 h-8 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">
                    Schedule Discovery Call
                  </h3>
                  <p className="text-muted-foreground text-sm">
                    30-minute technical discussion about your LLM system
                    requirements
                  </p>
                </div>

                <div className="w-full">
                  <BookConsultationButton size="lg" />
                </div>

                <div className="text-center mt-4">
                  <p className="text-xs text-muted-foreground">
                    30-minute consultation • Automatic timezone detection • Free
                    discovery call
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Secondary Options */}
            <Card>
              <CardContent className="p-8">
                <h3 className="text-xl font-semibold mb-6 text-center">
                  Other Ways to Connect
                </h3>

                <div className="space-y-4">
                  {/* Download Resume */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-5 h-5 text-primary"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">Download Resume</h4>
                      <p className="text-sm text-muted-foreground">
                        Full technical background and experience
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href="/resume">Download</a>
                    </Button>
                  </div>

                  {/* Direct Email */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-5 h-5 text-primary"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">Direct Email</h4>
                      <p className="text-sm text-muted-foreground">
                        serbyn.vitalii@gmail.com
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href="mailto:serbyn.vitalii@gmail.com">Email</a>
                    </Button>
                  </div>

                  {/* LinkedIn */}
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-5 h-5 text-primary"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">LinkedIn</h4>
                      <p className="text-sm text-muted-foreground">
                        Professional networking
                      </p>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href="https://www.linkedin.com/in/vitalii-serbyn-b517a083"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Connect
                      </a>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Response Time & Availability */}
          <div className="mt-12 text-center">
            <Card className="max-w-2xl mx-auto">
              <CardContent className="p-6">
                <div className="grid gap-6 sm:grid-cols-3 text-center">
                  <div>
                    <div className="text-2xl font-bold text-primary mb-1">
                      24hrs
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Response time
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary mb-1">
                      GMT+2
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Kyiv timezone
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary mb-1">
                      US/EU
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Client focus
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-6 border-t">
                  <p className="text-sm text-muted-foreground">
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    Currently available for new projects • Next availability:
                    February 2025
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Trust Signals */}
          <div className="mt-8 text-center">
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>NDA available</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>SOC 2 experience</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>£2M insurance</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>UK LTD registered</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
