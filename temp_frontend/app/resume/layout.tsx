import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata.resume();

export default function ResumeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
