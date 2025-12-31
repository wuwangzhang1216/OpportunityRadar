import { Radar } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex flex-col justify-center px-8 py-12 lg:px-20">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Link href="/" className="flex items-center justify-center gap-2 mb-8">
            <Radar className="h-10 w-10 text-blue-600" />
            <span className="text-2xl font-bold">OpportunityRadar</span>
          </Link>
          {children}
        </div>
      </div>

      {/* Right side - Branding */}
      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-blue-600 to-blue-800 p-12 items-center justify-center">
        <div className="max-w-md text-white">
          <h2 className="text-3xl font-bold mb-4">
            Find Your Perfect Hackathon
          </h2>
          <p className="text-blue-100 text-lg mb-8">
            Join thousands of developers who use OpportunityRadar to discover,
            match, and win hackathons.
          </p>
          <div className="space-y-4">
            <Feature text="AI-powered opportunity matching" />
            <Feature text="500+ active hackathons and grants" />
            <Feature text="Auto-generate winning materials" />
            <Feature text="Track your progress with pipelines" />
          </div>
        </div>
      </div>
    </div>
  );
}

function Feature({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 rounded-full bg-blue-300" />
      <span className="text-blue-100">{text}</span>
    </div>
  );
}
