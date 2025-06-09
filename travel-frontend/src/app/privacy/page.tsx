import Header from "../components/Header";
import Footer from "../components/Footer";

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>

          <div className="prose dark:prose-invert max-w-none">
            <p className="text-lg mb-6">Last updated: May 21, 2025</p>

            <p className="mb-6">
              This Privacy Policy describes how TravelAI (&quot;we&quot;,
              &quot;our&quot;, or &quot;us&quot;) collects, uses, and discloses
              your personal information when you use our website and services.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              Information We Collect
            </h2>
            <p className="mb-6">Privacy policy content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              How We Use Your Information
            </h2>
            <p className="mb-6">Privacy policy content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              Sharing Your Information
            </h2>
            <p className="mb-6">Privacy policy content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">Your Rights</h2>
            <p className="mb-6">Privacy policy content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">
              Changes to This Privacy Policy
            </h2>
            <p className="mb-6">Privacy policy content coming soon...</p>

            <h2 className="text-2xl font-bold mt-8 mb-4">Contact Us</h2>
            <p className="mb-6">
              If you have any questions about this Privacy Policy, please
              contact us at privacy@travelai.example.com.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
