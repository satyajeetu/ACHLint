import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";

const sans = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const mono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://satyajeetu.github.io/ACHLint/"),
  title: "ACHLint | ACH File Generator and Validator",
  description:
    "Generate ACH files from CSV and validate NACHA uploads before bank submission. Built for spreadsheet-driven payroll and payout workflows.",
  keywords: [
    "ACH file generator",
    "ACH validator",
    "NACHA validator",
    "CSV to ACH",
    "ACH file builder",
    "payroll ACH",
    "payout operations",
    "bank file validation",
  ],
  alternates: {
    canonical: "https://satyajeetu.github.io/ACHLint/",
  },
  openGraph: {
    title: "ACHLint | ACH File Generator and Validator",
    description:
      "Create ACH files from CSV and validate NACHA uploads before bank submission.",
    url: "https://satyajeetu.github.io/ACHLint/",
    siteName: "ACHLint",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ACHLint | ACH File Generator and Validator",
    description:
      "Create ACH files from CSV and validate NACHA uploads before bank submission.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
