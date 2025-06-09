import Header from "../components/Header";

export default function TermsOfService() {
  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>

          <div className="prose dark:prose-invert max-w-none">
            <p className="text-lg mb-6">Last updated: May 21, 2025</p>

            <p className="mb-6">
              Please read these Terms of Service carefully before using the
              TravelAI website and services operated by TravelAI.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              1. Acceptance of Terms
            </h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              2. Changes to Terms
            </h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              3. Access to the Service
            </h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              4. Intellectual Property
            </h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">5. Termination</h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              6. Limitation of Liability
            </h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">7. Governing Law</h2>
            <p className="mb-6">Terms of service content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">8. Contact Us</h2>
            <p className="mb-6">
              If you have any questions about these Terms, please contact us at
              terms@travelai.example.com.
            </p>
          </div>
        </div>
      </main>

      <footer className="py-8 bg-white dark:bg-black border-t border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4">
          <div className="text-center text-sm text-gray-500 dark:text-gray-400">
            © {new Date().getFullYear()} TravelAI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
