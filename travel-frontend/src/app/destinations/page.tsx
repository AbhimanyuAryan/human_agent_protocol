import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Destinations() {
  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">Popular Destinations</h1>

        <div className="text-center py-20">
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Destinations content coming soon...
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}
