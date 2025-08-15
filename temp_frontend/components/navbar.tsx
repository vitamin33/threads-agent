'use client';

import { useState } from 'react';
import Link from 'next/link';

const navigationLinks = [
  {
    name: 'Proof',
    href: '#proof' as const,
    description: 'Evidence of my work',
  },
  { name: 'Services', href: '#services' as const, description: 'What I offer' },
  {
    name: 'Case Studies',
    href: '/case-studies' as const,
    description: 'Project examples',
  },
  {
    name: 'Resume',
    href: '/resume' as const,
    description: 'Full work history',
  },
  {
    name: 'How to Pay',
    href: '/how-to-pay' as const,
    description: 'Payment methods',
  },
  { name: 'Contact', href: '#contact' as const, description: 'Get in touch' },
];

export function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
    // Prevent body scroll when mobile menu is open
    if (typeof window !== 'undefined') {
      document.body.classList.toggle('mobile-menu-open', !isMobileMenuOpen);
    }
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
    if (typeof window !== 'undefined') {
      document.body.classList.remove('mobile-menu-open');
    }
  };

  return (
    <nav
      className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-md supports-[backdrop-filter]:bg-white/60"
      aria-label="Main navigation"
    >
      <div className="container">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link
              href="/"
              className="flex items-center space-x-2 font-bold text-xl hover:text-blue-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 rounded-md p-1"
              aria-label="Serbyn.pro - Home"
            >
              <span className="font-mono text-blue-600">$</span>
              <span>serbyn.pro</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <ul className="flex items-center space-x-1" role="menubar">
              {navigationLinks.map(link => (
                <li key={link.name} role="none">
                  <Link
                    href={link.href as any}
                    className="btn btn-ghost px-3 py-2 text-sm"
                    role="menuitem"
                    aria-label={link.description}
                    onClick={
                      link.href.startsWith('#') ? closeMobileMenu : undefined
                    }
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              type="button"
              className="btn btn-ghost p-2"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              onClick={toggleMobileMenu}
            >
              <span className="sr-only">
                {isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              </span>
              {isMobileMenuOpen ? (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <div
        id="mobile-menu"
        className={`md:hidden transition-all duration-300 ease-in-out ${
          isMobileMenuOpen
            ? 'max-h-96 opacity-100'
            : 'max-h-0 opacity-0 overflow-hidden'
        }`}
        aria-hidden={!isMobileMenuOpen}
      >
        <div className="border-t border-gray-200 bg-white px-4 py-2 shadow-lg">
          <ul className="space-y-1" role="menu">
            {navigationLinks.map(link => (
              <li key={link.name} role="none">
                <Link
                  href={link.href as any}
                  className="block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-50 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
                  role="menuitem"
                  aria-label={link.description}
                  onClick={closeMobileMenu}
                >
                  <div>
                    <div className="font-medium">{link.name}</div>
                    <div className="text-sm text-gray-500">
                      {link.description}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </nav>
  );
}
