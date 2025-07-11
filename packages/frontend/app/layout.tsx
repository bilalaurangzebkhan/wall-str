import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { GoogleAnalytics } from "@next/third-parties/google";

import QueryClientProvider from "@/providers/QueryClientProvider";

import "./globals.css";
import { settings } from "@/conf";
import { api } from "@/api";
import ConfigProvider from "@/providers/ConfigProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Wallstr.chat: AI-Powered Equity Research",
  description: "AI-Powered Document Analysis",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { data: config } = await api.default.getConfig();

  return (
    <html lang="en" suppressHydrationWarning>
      {settings.GA_TAG ? <GoogleAnalytics gaId={settings.GA_TAG!} /> : null}
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ConfigProvider config={config}>
          <QueryClientProvider>
            <ThemeProvider>{children}</ThemeProvider>
          </QueryClientProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}
