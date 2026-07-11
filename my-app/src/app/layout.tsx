import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { SidebarProvider } from "@/Components/SideBar";

export const metadata: Metadata = {
  title: "Sales Automation",
  description: "Sales Automation Dashboard",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="light">
      <body className="antialiased">
        <SidebarProvider>{children}</SidebarProvider>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              borderRadius: "12px",
              background: "#fff",
              color: "#111827",
            },
          }}
        />
      </body>
    </html>
  );
}
