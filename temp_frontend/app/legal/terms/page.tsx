import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata.terms();

export default function TermsPage() {
  const lastUpdated = 'January 15, 2025';

  return (
    <div className="min-h-screen py-16">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight mb-4">
              Terms of Service
            </h1>
            <p className="text-muted-foreground">Last updated: {lastUpdated}</p>
          </div>

          <div className="space-y-6">
            {/* Service Agreement */}
            <Card>
              <CardHeader>
                <CardTitle>Service Agreement</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p>
                  These terms govern the provision of AI/ML engineering services
                  by Easelect LTD, a company incorporated in England and Wales
                  (Company Number: 15983917).
                </p>
                <div className="bg-muted/50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">Services Provided</h3>
                  <ul className="text-sm space-y-1">
                    <li>• AI/ML system design and implementation</li>
                    <li>• Large Language Model deployment and optimization</li>
                    <li>• MLOps pipeline development and maintenance</li>
                    <li>• Technical consulting and code review</li>
                    <li>• Performance optimization and cost reduction</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Service Delivery */}
            <Card>
              <CardHeader>
                <CardTitle>Service Delivery Terms</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Project Execution</h3>
                  <ul className="text-sm space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>
                        All work performed remotely unless otherwise agreed
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>
                        Deliverables provided as agreed in project scope
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>Regular progress updates and communication</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>
                        Source code ownership transferred upon full payment
                      </span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">
                    Client Responsibilities
                  </h3>
                  <ul className="text-sm space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>Provide necessary access to systems and data</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>Ensure compliance with applicable regulations</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                      <span>Timely review and feedback on deliverables</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Payment & Billing */}
            <Card>
              <CardHeader>
                <CardTitle>Payment & Billing</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <h3 className="font-semibold mb-2">Payment Terms</h3>
                    <ul className="text-sm space-y-1">
                      <li>• Net 15 days from invoice date</li>
                      <li>• Late fees: 1.5% per month</li>
                      <li>• Payments in USD, EUR, or GBP</li>
                      <li>• VAT added as applicable</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Project Structure</h3>
                    <ul className="text-sm space-y-1">
                      <li>• Fixed projects: 50% upfront</li>
                      <li>• Time & materials: Monthly billing</li>
                      <li>• Retainers: Quarterly terms available</li>
                      <li>• Expenses billed separately</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Intellectual Property */}
            <Card>
              <CardHeader>
                <CardTitle>Intellectual Property</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Work Product</h3>
                  <p className="text-sm mb-3">
                    All custom code, documentation, and deliverables created
                    specifically for your project become your property upon full
                    payment.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Pre-existing IP</h3>
                  <p className="text-sm">
                    Tools, frameworks, and general methodologies developed prior
                    to engagement remain our intellectual property but are
                    licensed for your use as part of the delivered solution.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Limitation of Liability */}
            <Card>
              <CardHeader>
                <CardTitle>Limitation of Liability</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">Important Notice</h3>
                  <p className="text-sm">
                    Our total liability for any claims arising from our services
                    is limited to the total amount paid for the specific project
                    or service period in question.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Professional Indemnity</h3>
                  <p className="text-sm">
                    We operate with standard business practices to cover errors
                    and omissions in our professional services.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Force Majeure</h3>
                  <p className="text-sm">
                    Neither party shall be liable for delays or failures due to
                    circumstances beyond reasonable control, including but not
                    limited to natural disasters, war, or government actions.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Termination */}
            <Card>
              <CardHeader>
                <CardTitle>Termination</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Project Completion</h3>
                    <p className="text-sm">
                      Services are complete when all agreed deliverables have
                      been provided and accepted by the client.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Early Termination</h3>
                    <p className="text-sm">
                      Either party may terminate with 14 days written notice.
                      Client is responsible for payment of work completed to
                      termination date.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Contact */}
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-muted/50 p-4 rounded-lg">
                  <div className="space-y-2 text-sm">
                    <p>
                      <strong>Easelect LTD</strong>
                    </p>
                    <p>
                      Office 12, Initial Business Centre, Wilson Business Park
                    </p>
                    <p>Manchester, M40 8WN, United Kingdom</p>
                    <p>Email: serbyn.vitalii@gmail.com</p>
                    <p>Company Number: 15983917</p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  These terms are governed by English law and subject to the
                  exclusive jurisdiction of English courts.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
