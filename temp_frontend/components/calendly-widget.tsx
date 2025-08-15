'use client';

import { useState } from 'react';
import { PopupWidget, InlineWidget } from 'react-calendly';
import { Button } from '@/components/ui/button';
import { Calendar, ExternalLink } from 'lucide-react';

interface CalendlyButtonProps {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'default' | 'lg';
  className?: string;
  children?: React.ReactNode;
  mode?: 'popup' | 'external' | 'inline';
}

const CALENDLY_URL = 'https://calendly.com/serbyn-vitalii/consulting';

export function CalendlyButton({
  variant = 'default',
  size = 'default',
  className = '',
  children = 'Book a Call',
  mode = 'popup',
}: CalendlyButtonProps) {
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  if (mode === 'external') {
    return (
      <Button variant={variant} size={size} className={className} asChild>
        <a
          href={CALENDLY_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2"
        >
          <Calendar className="h-4 w-4" />
          {children}
          <ExternalLink className="h-3 w-3" />
        </a>
      </Button>
    );
  }

  if (mode === 'popup') {
    // For build safety, redirect to external for now
    return (
      <Button variant={variant} size={size} className={className} asChild>
        <a
          href={CALENDLY_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2"
        >
          <Calendar className="h-4 w-4" />
          {children}
          <ExternalLink className="h-3 w-3" />
        </a>
      </Button>
    );
  }

  // mode === 'inline' - not used in buttons but available for dedicated pages
  return null;
}

// Inline widget for dedicated booking pages
export function CalendlyInline({ className = '' }: { className?: string }) {
  return (
    <div className={className}>
      <InlineWidget
        url={CALENDLY_URL}
        styles={{
          height: '700px',
          width: '100%',
        }}
      />
    </div>
  );
}

// Prefab buttons for common use cases
export function BookConsultationButton({
  size = 'lg',
}: {
  size?: 'sm' | 'default' | 'lg';
}) {
  return (
    <CalendlyButton
      size={size}
      mode="external"
      className="w-full sm:w-auto min-w-[160px] font-semibold"
    >
      Book Consultation
    </CalendlyButton>
  );
}

export function ScheduleCallButton({
  variant = 'outline',
  size = 'default',
}: {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'default' | 'lg';
}) {
  return (
    <CalendlyButton variant={variant} size={size} mode="external">
      Schedule a Call
    </CalendlyButton>
  );
}
