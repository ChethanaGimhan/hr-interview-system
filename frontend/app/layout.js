import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "HR Interview System",
  description: "Turn a candidate CV into interview questions with rubrics",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
            <Link href="/" className="text-lg font-semibold">
              HR Interview System
            </Link>
            <nav className="flex gap-6 text-sm text-slate-600">
              <Link href="/" className="hover:text-slate-900">
                New questionnaire
              </Link>
              <Link href="/history" className="hover:text-slate-900">
                History
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-10">{children}</main>

        <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500">
          Built by Chethana Gimhan
        </footer>
      </body>
    </html>
  );
}
