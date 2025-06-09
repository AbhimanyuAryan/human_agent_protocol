import Image from "next/image";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="py-8 bg-white dark:bg-black border-t border-gray-200 dark:border-gray-800">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <Image
              src="/vercel.svg"
              alt="TravelAI Logo"
              width={20}
              height={20}
              className="dark:invert"
            />
            <span className="font-bold">TravelAI</span>
          </div>

          <div className="flex gap-8 flex-wrap justify-center">
            <Link
              href="/about"
              className="text-sm hover:underline hover:underline-offset-4">
              About Us
            </Link>
            <Link
              href="/destinations"
              className="text-sm hover:underline hover:underline-offset-4">
              Destinations
            </Link>
            <Link
              href="/privacy"
              className="text-sm hover:underline hover:underline-offset-4">
              Privacy Policy
            </Link>
            <Link
              href="/terms"
              className="text-sm hover:underline hover:underline-offset-4">
              Terms of Service
            </Link>
          </div>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400">
          © {new Date().getFullYear()} TravelAI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
