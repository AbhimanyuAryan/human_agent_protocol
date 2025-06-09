import Image from "next/image";
import Link from "next/link";

interface HeaderProps {
  transparent?: boolean;
}

export default function Header({ transparent = false }: HeaderProps) {
  return (
    <header
      className={`w-full ${
        transparent
          ? "absolute top-0 z-10"
          : "bg-white dark:bg-black border-b border-gray-200 dark:border-gray-800"
      }`}>
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/vercel.svg"
            alt="Travel Logo"
            width={24}
            height={24}
            className="dark:invert"
          />
          <span className="font-bold text-lg">TravelAI</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/"
            className="text-sm font-medium hover:underline underline-offset-4">
            Home
          </Link>
          <Link
            href="/destinations"
            className="text-sm font-medium hover:underline underline-offset-4">
            Destinations
          </Link>
          <Link
            href="/copilotkit"
            className="text-sm font-medium hover:underline underline-offset-4">
            Trip Planner
          </Link>
          <Link
            href="/about"
            className="text-sm font-medium hover:underline underline-offset-4">
            About
          </Link>
        </nav>

        <div className="flex gap-3">
          <Link
            href="/copilotkit"
            className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm h-10 px-4">
            Plan a Trip
          </Link>
        </div>
      </div>
    </header>
  );
}
