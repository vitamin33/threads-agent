import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata.privacy();

export default function PrivacyPage() {
  const lastUpdated = 'January 15, 2025';

  return (
    <div className="min-h-screen py-16">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight mb-4">
              Privacy Policy
            </h1>
            <p className="text-muted-foreground">Last updated: {lastUpdated}</p>
          </div>

          <div className="prose prose-sm max-w-none space-y-6">
            {/* Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Data Protection Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p>
                  Easelect LTD (&quot;we&quot;, &quot;our&quot;, or
                  &quot;us&quot;) is committed to protecting your privacy. This
                  policy explains how we collect, use, and protect your personal
                  information in compliance with UK GDPR and applicable data
                  protection laws.
                </p>
                <div className="bg-muted/50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">Key Principles</h3>
                  <ul className="text-sm space-y-1">
                    <li>• We collect only necessary information</li>
                    <li>• Your data is never sold to third parties</li>
                    <li>• You have full control over your personal data</li>
                    <li>• We implement appropriate security measures</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Information We Collect */}
            <Card>
              <CardHeader>
                <CardTitle>Information We Collect</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Contact Information</h3>
                  <ul className="text-sm space-y-1 ml-4">
                    <li>• Name and email address (when you contact us)</li>
                    <li>• Company information (for business inquiries)</li>
                    <li>• Project requirements and technical specifications</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Website Analytics</h3>
                  <ul className="text-sm space-y-1 ml-4">
                    <li>• Page views and navigation patterns (anonymized)</li>
                    <li>• Browser type and device information</li>
                    <li>• Referral sources (how you found our site)</li>
                  </ul>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm">
                    <strong>Note:</strong> We use privacy-focused analytics
                    (Plausible) that doesn&apos;t require cookies or track
                    personal information.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* How We Use Information */}
            <Card>
              <CardHeader>
                <CardTitle>How We Use Your Information</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-sm space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                    <span>
                      Respond to your inquiries and provide requested services
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                    <span>Communicate about projects and service delivery</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                    <span>Send invoices and handle payment processing</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                    <span>
                      Improve our website and services (anonymized analytics)
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                    <span>
                      Comply with legal obligations and business requirements
                    </span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Your Rights */}
            <Card>
              <CardHeader>
                <CardTitle>Your Data Rights (GDPR)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">
                  Under UK GDPR, you have the following rights:
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h3 className="font-semibold mb-2">Access & Control</h3>
                    <ul className="text-sm space-y-1">
                      <li>• Right to access your data</li>
                      <li>• Right to rectification</li>
                      <li>• Right to erasure</li>
                      <li>• Right to data portability</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Processing Rights</h3>
                    <ul className="text-sm space-y-1">
                      <li>• Right to restrict processing</li>
                      <li>• Right to object</li>
                      <li>• Right to withdraw consent</li>
                      <li>• Right to lodge a complaint</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Contact for Data Requests */}
            <Card>
              <CardHeader>
                <CardTitle>Data Requests & Contact</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p>
                  To exercise your data rights or for any privacy-related
                  questions, please contact us:
                </p>
                <div className="bg-muted/50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm">
                    <p>
                      <strong>Email:</strong> serbyn.vitalii@gmail.com
                    </p>
                    <p>
                      <strong>Mail:</strong> Easelect LTD, Office 12, Initial
                      Business Centre, Wilson Business Park, Manchester, M40 8WN
                    </p>
                    <p>
                      <strong>Response Time:</strong> We will respond within 30
                      days
                    </p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  You can also contact the UK Information Commissioner&apos;s
                  Office (ICO) if you have concerns about how we handle your
                  data.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
