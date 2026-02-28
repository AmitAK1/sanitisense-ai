import Link from 'next/link';
import {
  Shield,
  Camera,
  Brain,
  Users,
  BarChart3,
  MapPin,
  Zap,
  ArrowRight,
  CheckCircle,
  Globe,
} from 'lucide-react';

const features = [
  {
    icon: Camera,
    title: 'Photo-Based Reporting',
    desc: 'Citizens snap a photo of sanitation issues. AI instantly classifies type, severity, and health risk.',
  },
  {
    icon: Brain,
    title: 'Amazon Bedrock AI',
    desc: 'Claude Sonnet 4 vision model analyzes images, generates descriptions, and provides epidemic risk assessments.',
  },
  {
    icon: Users,
    title: 'Smart Task Assignment',
    desc: 'Auto-generates prioritized tasks for field workers based on AI severity scores and SLA thresholds.',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Dashboard',
    desc: 'Municipal admins get live stats, ward-level heatmaps, trend charts, and worker leaderboards.',
  },
  {
    icon: MapPin,
    title: 'Ward-Level Heatmaps',
    desc: 'Geographic visualization of sanitation hotspots across all 24 wards for proactive resource allocation.',
  },
  {
    icon: Zap,
    title: 'Before/After Validation',
    desc: 'AI compares before and after photos to verify task completion — no human bias in quality checks.',
  },
];

const stats = [
  { value: '94.6%', label: 'AI Accuracy' },
  { value: '6.4h', label: 'Avg Resolution' },
  { value: '24', label: 'Wards Covered' },
  { value: '4.2★', label: 'Citizen Rating' },
];

const howItWorks = [
  { step: '1', title: 'Citizen Reports', desc: 'Upload a photo of the sanitation issue with GPS location' },
  { step: '2', title: 'AI Analysis', desc: 'Bedrock Vision classifies severity, category, and health risk in seconds' },
  { step: '3', title: 'Task Created', desc: 'Priority task auto-assigned to nearest available field worker' },
  { step: '4', title: 'Resolved & Verified', desc: 'Worker fixes issue, uploads proof — AI validates completion' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* ==================== HERO ==================== */}
      <section className="relative overflow-hidden bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-20 w-96 h-96 bg-amber-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-1.5 mb-6 text-sm">
              <Shield className="h-4 w-4" />
              <span>AWS AI for Bharat Hackathon 2026</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Saniti<span className="text-amber-300">Sense</span> AI
            </h1>
            <p className="text-xl md:text-2xl text-emerald-100 mb-4 font-light">
              The Civic Operating System for Urban Sanitation
            </p>
            <p className="text-emerald-200 mb-10 max-w-xl mx-auto">
              AI-powered platform that transforms how Indian cities manage sanitation — from citizen
              reports to field resolution, verified by Amazon Bedrock.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/report"
                className="inline-flex items-center justify-center gap-2 bg-white text-emerald-700 font-semibold px-8 py-3.5 rounded-xl hover:bg-emerald-50 transition-colors shadow-lg"
              >
                Report an Issue
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 bg-emerald-800/50 backdrop-blur text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-emerald-800/70 transition-colors border border-white/20"
              >
                View Dashboard
                <BarChart3 className="h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ==================== STATS BAR ==================== */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {stats.map((s) => (
              <div key={s.label}>
                <div className="text-3xl font-bold text-emerald-600">{s.value}</div>
                <div className="text-sm text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== PROBLEM STATEMENT ==================== */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">The Problem</h2>
            <p className="text-lg text-gray-600">
              Indian cities generate <span className="font-semibold text-gray-900">1.5 lakh tonnes</span> of
              municipal solid waste daily. Manual reporting causes delays of{' '}
              <span className="font-semibold text-red-600">3-7 days</span>. Missed hotspots trigger
              preventable disease outbreaks.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              { num: '62M+', text: 'Tonnes of waste generated annually in urban India' },
              { num: '~40%', text: 'Of waste remains unprocessed in smaller cities' },
              { num: '3-7 days', text: 'Average delay with manual complaint systems' },
            ].map((item) => (
              <div key={item.num} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
                <div className="text-2xl font-bold text-red-500 mb-2">{item.num}</div>
                <p className="text-sm text-gray-600">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== HOW IT WORKS ==================== */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {howItWorks.map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-14 h-14 bg-emerald-100 text-emerald-700 rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== FEATURES ==================== */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Key Features</h2>
          <p className="text-center text-gray-500 mb-12 max-w-xl mx-auto">
            Built on AWS serverless architecture with Amazon Bedrock at its core.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-4">
                  <f.icon className="h-6 w-6 text-emerald-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== TECH STACK ==================== */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">AWS-Powered Architecture</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { service: 'Amazon Bedrock', detail: 'Claude Sonnet 4 + RAG' },
              { service: 'AWS Lambda', detail: '6 Serverless Functions' },
              { service: 'API Gateway', detail: 'REST API (prod stage)' },
              { service: 'DynamoDB', detail: 'Single-Table Design' },
              { service: 'S3', detail: 'Media & Knowledge Store' },
              { service: 'Rekognition', detail: 'Image Label Detection' },
              { service: 'SAM / CloudFormation', detail: 'IaC Deployment' },
              { service: 'Amplify', detail: 'Frontend Hosting' },
            ].map((t) => (
              <div key={t.service} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                <CheckCircle className="h-5 w-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium text-gray-900 text-sm">{t.service}</div>
                  <div className="text-xs text-gray-500">{t.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== CTA ==================== */}
      <section className="bg-emerald-600 py-16">
        <div className="max-w-3xl mx-auto px-4 text-center text-white">
          <Globe className="h-12 w-12 mx-auto mb-4 opacity-80" />
          <h2 className="text-3xl font-bold mb-4">Ready to Make Your City Cleaner?</h2>
          <p className="text-emerald-100 mb-8">
            Join thousands of citizens using AI to report and resolve sanitation issues faster.
          </p>
          <Link
            href="/report"
            className="inline-flex items-center gap-2 bg-white text-emerald-700 font-semibold px-8 py-3.5 rounded-xl hover:bg-emerald-50 transition-colors shadow-lg"
          >
            Report Now
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* ==================== FOOTER ==================== */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-emerald-500" />
            <span className="text-white font-semibold">SanitiSense AI</span>
          </div>
          <p>Built by Team Swadeshi Coders for AWS AI for Bharat Hackathon 2026</p>
          <p className="mt-1">Powered by Amazon Bedrock &middot; Claude Sonnet 4 &middot; DynamoDB &middot; Lambda</p>
        </div>
      </footer>
    </div>
  );
}
