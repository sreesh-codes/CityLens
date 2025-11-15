import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { GeistSans } from 'geist/font/sans'

import './globals.css'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Footer } from '@/components/layout/footer'
import { Navbar } from '@/components/layout/navbar'
import { MobileNav } from '@/components/layout/mobile-nav'
import { Providers } from '@/components/providers'
import { cn } from '@/lib/utils'

export const metadata: Metadata = {
  title: 'CityLens • Dubai Civic AI',
  description: 'AI-powered urban issue detection for Dubai residents.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          GeistSans.className,
          'bg-slate-950 text-white antialiased'
        )}
      >
        <Providers>
          <div className="grid-bg min-h-screen w-full pb-24 md:pb-10">
            <Navbar />
            <main className="w-full px-0">{children}</main>
            <Footer />
            <MobileNav />
          </div>
        </Providers>
      </body>
    </html>
  )
}
