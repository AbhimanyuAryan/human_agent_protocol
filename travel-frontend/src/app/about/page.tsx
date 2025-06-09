import Header from "../components/Header";
import Footer from "../components/Footer";

export default function About() {
  return (
    <div className="min-h-screen flex flex-col font-[family-name:var(--font-geist-sans)]">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">About TravelAI</h1>

          <div className="prose dark:prose-invert max-w-none">
            <p className="text-lg mb-6">
              TravelAI is an innovative travel planning platform that leverages
              artificial intelligence to help travelers plan their perfect
              trips. Our mission is to make travel planning simple,
              personalized, and enjoyable.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">Our Story</h2>
            <p className="mb-6">
              Founded in 2025, TravelAI was created by a team of travel
              enthusiasts and AI engineers who were frustrated with the
              complexity of planning trips across multiple platforms. We set out
              to build a comprehensive solution that combines the power of AI
              with human expertise to create the ultimate travel planning
              experience.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">How It Works</h2>
            <p className="mb-6">
              Our AI-powered assistant analyzes your preferences, budget, and
              travel style to recommend destinations, accommodations,
              activities, and dining options that match your unique needs.
              Whether you&apos;re planning a family vacation, a romantic
              getaway, or a solo adventure, TravelAI helps you create the
              perfect itinerary.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">Our Technology</h2>
            <p className="mb-6">
              TravelAI uses state-of-the-art language models and machine
              learning algorithms to understand your travel preferences and
              provide personalized recommendations. Our platform continuously
              learns from user interactions to improve its suggestions and
              create better travel experiences.
            </p>

            <h2 className="text-2xl font-bold mt-8 mb-4">Get in Touch</h2>
            <p className="mb-6">
              We&apos;d love to hear from you! If you have any questions,
              feedback, or suggestions, please don&apos;t hesitate to contact
              our team at support@travelai.example.com.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
