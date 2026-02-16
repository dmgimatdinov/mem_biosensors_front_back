import type { Metadata } from 'next'

import './globals.css'

export const metadata: Metadata = {
  title: 'BioSensor Passport Manager',
  description: 'Manage passports for memristive biosensors - data entry, analysis, and export',
  generator: 'v0.app',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
