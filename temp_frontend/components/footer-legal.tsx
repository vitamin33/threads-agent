import Link from 'next/link';

export function FooterLegal() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 bg-gray-50 no-print">
      <div className="container py-12">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Company Information */}
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Easelect LTD</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p>Company Number: 15983917</p>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">
                Registered Office:
              </p>
              <address className="not-italic">
                Office 12, Initial Business Centre
                <br />
                Wilson Business Park
                <br />
                Manchester, M40 8WN
                <br />
                United Kingdom
              </address>
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Contact</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p>
                  <a
                    href="mailto:serbyn.vitalii@gmail.com"
                    className="hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                  >
                    serbyn.vitalii@gmail.com
                  </a>
                </p>
                <p>Remote from Kyiv, Ukraine</p>
                <p>Serving US/EU clients</p>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              <p>Business Hours: Monday-Friday, 9AM-6PM GMT</p>
            </div>
          </div>

          {/* Legal Links */}
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Legal</h3>
              <nav className="space-y-2 text-sm" aria-label="Legal pages">
                <Link
                  href={'/legal/privacy' as any}
                  className="block text-gray-600 hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                >
                  Privacy Policy
                </Link>
                <Link
                  href={'/legal/terms' as any}
                  className="block text-gray-600 hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                >
                  Terms of Service
                </Link>
                <Link
                  href={'/legal/cookies' as any}
                  className="block text-gray-600 hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                >
                  Cookie Policy
                </Link>
              </nav>
            </div>
            <div className="text-sm text-gray-600"></div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="text-sm text-gray-600">
              <p>
                © {currentYear} Easelect LTD. All rights reserved.
                <span className="ml-2 inline-block">
                  <span className="sr-only">Location:</span>
                  Incorporated in England & Wales
                </span>
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <a
                href="https://find-and-update.company-information.service.gov.uk/company/15983917"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
                aria-label="View company information at Companies House (opens in new tab)"
              >
                Companies House
                <span className="sr-only"> (opens in new tab)</span>
              </a>
              <span className="text-gray-300">|</span>
              <span className="font-mono text-xs">UK LTD</span>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Notice */}
      <div className="bg-gray-100 py-3">
        <div className="container">
          <p className="text-xs text-gray-600 text-center">
            This website complies with UK GDPR, Companies Act 2006, and VAT
            regulations.
            <span className="ml-2">
              <Link
                href={'/legal/compliance' as any}
                className="hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded"
              >
                View compliance details
              </Link>
            </span>
          </p>
        </div>
      </div>
    </footer>
  );
}
