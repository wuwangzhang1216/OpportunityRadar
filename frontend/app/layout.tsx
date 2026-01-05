import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "driver.js/dist/driver.css";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui/toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OpportunityRadar - Discover Your Next Hackathon",
  description:
    "AI-powered platform to discover, match, and prepare for hackathons and funding opportunities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
