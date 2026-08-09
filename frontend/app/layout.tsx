import type { Metadata } from "next";
import { JetBrains_Mono, Karla, Space_Grotesk } from "next/font/google";

import { NavBar } from "@/components/layout/NavBar";
import { AuthProvider } from "@/providers/AuthProvider";
import { QueryProvider } from "@/providers/QueryProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { NO_FLASH_THEME_SCRIPT } from "@/lib/theme";

import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const karla = Karla({
  variable: "--font-karla",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Bac Exercise Generator",
  description:
    "Exerciții de informatică pentru bacalaureat, generate și verificate automat.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="ro"
      className={`${spaceGrotesk.variable} ${karla.variable} ${jetBrainsMono.variable}`}
    >
      <head>
        {/* Blocking, before paint: applies the stored theme class to avoid a flash of the wrong theme. */}
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_THEME_SCRIPT }} />
      </head>
      <body className="min-h-screen">
        <AuthProvider>
          <QueryProvider>
            <ThemeProvider>
              <NavBar />
              {children}
            </ThemeProvider>
          </QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
