import Link from "next/link";
import { ArrowRight, Radar, Target, Zap, Trophy } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radar className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold">OpportunityRadar</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-gray-600 hover:text-gray-900 transition"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Discover Your Perfect{" "}
          <span className="text-blue-600">Hackathon</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          AI-powered matching to find hackathons that fit your skills, schedule,
          and goals. Generate winning materials in minutes.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/signup"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition flex items-center gap-2"
          >
            Start Free <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            href="/opportunities"
            className="border border-gray-300 px-8 py-3 rounded-lg text-lg font-medium hover:border-gray-400 transition"
          >
            Browse Opportunities
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">
          Everything You Need to Win
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Target className="h-10 w-10 text-blue-600" />}
            title="Smart Matching"
            description="Our AI analyzes your profile and matches you with opportunities where you'll thrive."
          />
          <FeatureCard
            icon={<Zap className="h-10 w-10 text-blue-600" />}
            title="AI Materials"
            description="Generate README, pitch scripts, and demo guides tailored to each hackathon."
          />
          <FeatureCard
            icon={<Trophy className="h-10 w-10 text-blue-600" />}
            title="Track Progress"
            description="Kanban-style pipeline to track your applications from discovery to victory."
          />
        </div>
      </section>

      {/* Stats */}
      <section className="bg-blue-600 text-white py-16">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">500+</div>
              <div className="text-blue-200">Active Opportunities</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">12</div>
              <div className="text-blue-200">Data Sources</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">AI</div>
              <div className="text-blue-200">Powered Matching</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to Find Your Next Win?</h2>
        <p className="text-gray-600 mb-8">
          Create your profile in 2 minutes and get matched instantly.
        </p>
        <Link
          href="/signup"
          className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition inline-flex items-center gap-2"
        >
          Get Started Free <ArrowRight className="h-5 w-5" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-6 text-center text-gray-600">
          <p>&copy; 2024 OpportunityRadar. Built for hackers, by hackers.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
