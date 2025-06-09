import Image from "next/image";
import Link from "next/link";
import Header from "./components/Header";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />

      {/* Hero Section */}
      <section className="relative h-[80vh] w-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center">
        <div className="absolute inset-0 bg-black/30 z-0"></div>
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-2xl text-white">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6">
              Explore the World with AI-Powered Travel Planning
            </h1>
            <p className="text-xl mb-8 opacity-90">
              Get personalized travel recommendations and plan your perfect trip
              with our AI travel assistant.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/copilotkit"
                className="rounded-full border border-solid border-transparent bg-white text-blue-600 hover:bg-blue-50 font-medium text-sm sm:text-base h-12 px-6 flex items-center justify-center">
                Plan Your Trip
              </Link>
              <Link
                href="/destinations"
                className="rounded-full border border-solid border-white hover:bg-white/10 text-white font-medium text-sm sm:text-base h-12 px-6 flex items-center justify-center">
                Explore Destinations
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white dark:bg-black">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">
            Why Choose TravelAI
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
                <Image
                  src="/globe.svg"
                  alt="Personalized icon"
                  width={24}
                  height={24}
                  className="dark:invert"
                />
              </div>
              <h3 className="text-xl font-bold mb-2">
                Personalized Recommendations
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get travel suggestions tailored to your preferences, budget, and
                travel style.
              </p>
            </div>

            <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mb-4">
                <Image
                  src="/window.svg"
                  alt="AI icon"
                  width={24}
                  height={24}
                  className="dark:invert"
                />
              </div>
              <h3 className="text-xl font-bold mb-2">AI-Powered Planning</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Our advanced AI assistant helps you create the perfect itinerary
                in seconds.
              </p>
            </div>

            <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-4">
                <Image
                  src="/file.svg"
                  alt="Save icon"
                  width={24}
                  height={24}
                  className="dark:invert"
                />
              </div>
              <h3 className="text-xl font-bold mb-2">Seamless Experience</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Save and modify your travel plans with ease, all in one place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gray-100 dark:bg-gray-900">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to start your journey?
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
            Plan your next adventure with our AI-powered travel assistant and
            discover new destinations.
          </p>
          <Link
            href="/copilotkit"
            className="rounded-full border border-solid border-transparent bg-foreground text-background hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-base h-12 px-8 inline-flex items-center justify-center">
            Get Started Now
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
