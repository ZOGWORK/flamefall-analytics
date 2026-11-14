import type { Metadata, Viewport } from "next";
import { IBM_Plex_Sans, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import { Ambient } from "@/components/console/fx";
import { Motion } from "@/components/shell/motion";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

// Self-hosted at build time: the browser makes no request to a font service.
const grotesk = Space_Grotesk({ variable: "--font-grotesk", subsets: ["latin"], weight: ["500", "600", "700"] });
const plex = IBM_Plex_Sans({ variable: "--font-plex", subsets: ["latin"], weight: ["400", "500", "600"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"], weight: ["400", "500", "700"] });

export const metadata: Metadata = {
  title: { default: "Flamefall Analytics", template: "%s · Flamefall Analytics" },
  description:
    "What microgravity combustion experiments measured, with a source under every number and an explicit “no data” where nobody ran the test.",
};

export const viewport: Viewport = { themeColor: "#0B0F14", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`dark ${grotesk.variable} ${plex.variable} ${jetbrains.variable} h-full antialiased`}>
      <body className="min-h-full">
        <Ambient />
        <Motion>
          <TooltipProvider>{children}</TooltipProvider>
        </Motion>
      </body>
    </html>
  );
}
