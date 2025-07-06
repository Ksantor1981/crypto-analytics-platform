import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import { 
  ChartBarIcon, 
  CurrencyDollarIcon, 
  ShieldCheckIcon, 
  BoltIcon,
  StarIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'Real-time Signal Analysis',
    description: 'Track and analyze cryptocurrency trading signals from multiple Telegram channels in real-time.',
    icon: BoltIcon,
  },
  {
    name: 'Performance Metrics',
    description: 'Comprehensive analytics including accuracy rates, ROI calculations, and success tracking.',
    icon: ChartBarIcon,
  },
  {
    name: 'Risk Management',
    description: 'Advanced risk assessment tools to help you make informed trading decisions.',
    icon: ShieldCheckIcon,
  },
  {
    name: 'Profit Optimization',
    description: 'ML-powered predictions to maximize your trading profits and minimize losses.',
    icon: CurrencyDollarIcon,
  },
];

const testimonials = [
  {
    name: 'Alex Johnson',
    role: 'Crypto Trader',
    content: 'This platform has transformed my trading strategy. The signal analysis is incredibly accurate.',
    rating: 5,
  },
  {
    name: 'Sarah Chen',
    role: 'Investment Advisor',
    content: 'The performance metrics and risk management tools are exactly what I needed for my clients.',
    rating: 5,
  },
  {
    name: 'Michael Rodriguez',
    role: 'Day Trader',
    content: 'Real-time analysis and ML predictions have significantly improved my trading results.',
    rating: 5,
  },
];

export default function Home() {
  const [email, setEmail] = useState('');

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement newsletter signup
    console.log('Newsletter signup:', email);
    setEmail('');
  };

  return (
    <>
      <Head>
        <title>Crypto Analytics Platform - Advanced Trading Signal Analysis</title>
        <meta name="description" content="Track, analyze, and optimize your cryptocurrency trading with our advanced signal analysis platform. Real-time data, ML predictions, and comprehensive analytics." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="bg-white">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 justify-between items-center">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-2xl font-bold gradient-text">CryptoAnalytics</h1>
                </div>
              </div>
              <div className="hidden md:block">
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link href="#features" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Features
                  </Link>
                  <Link href="#pricing" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    Pricing
                  </Link>
                  <Link href="#about" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                    About
                  </Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/auth/login" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                  Sign In
                </Link>
                <Link href="/auth/register" className="btn btn-primary btn-sm">
                  Get Started
                </Link>
              </div>
            </div>
          </nav>
        </header>

        {/* Hero Section */}
        <section className="relative bg-gradient-to-r from-primary-600 to-primary-800 text-white">
          <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
                Advanced Crypto Trading
                <span className="block text-primary-200">Signal Analysis</span>
              </h1>
              <p className="mx-auto mt-6 max-w-2xl text-xl text-primary-100">
                Track, analyze, and optimize your cryptocurrency trading with real-time signal analysis, 
                ML-powered predictions, and comprehensive performance metrics.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <Link href="/auth/register" className="btn btn-lg bg-white text-primary-600 hover:bg-gray-100">
                  Start Free Trial
                </Link>
                <Link href="#features" className="btn btn-lg bg-transparent border-2 border-white text-white hover:bg-white hover:text-primary-600">
                  Learn More <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 bg-gray-50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                Everything you need to succeed
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                Comprehensive tools and analytics to maximize your trading potential
              </p>
            </div>
            <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <div key={feature.name} className="card fade-in">
                  <div className="card-body text-center">
                    <feature.icon className="mx-auto h-12 w-12 text-primary-600 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.name}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-24 bg-primary-600">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 text-center text-white">
              <div>
                <div className="text-4xl font-bold">98%</div>
                <div className="mt-2 text-primary-200">Signal Accuracy</div>
              </div>
              <div>
                <div className="text-4xl font-bold">50+</div>
                <div className="mt-2 text-primary-200">Monitored Channels</div>
              </div>
              <div>
                <div className="text-4xl font-bold">10K+</div>
                <div className="mt-2 text-primary-200">Active Users</div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="py-24 bg-white">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                What our users say
              </h2>
            </div>
            <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3">
              {testimonials.map((testimonial, index) => (
                <div key={index} className="card">
                  <div className="card-body">
                    <div className="flex items-center mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <StarIcon key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                      ))}
                    </div>
                    <p className="text-gray-600 mb-4">"{testimonial.content}"</p>
                    <div>
                      <div className="font-semibold text-gray-900">{testimonial.name}</div>
                      <div className="text-sm text-gray-500">{testimonial.role}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter */}
        <section className="bg-gray-50 py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900">
                Stay updated with market insights
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                Get the latest crypto trading signals and market analysis delivered to your inbox.
              </p>
              <form onSubmit={handleNewsletterSubmit} className="mt-8 flex max-w-md mx-auto">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="input flex-1 rounded-r-none"
                  required
                />
                <button type="submit" className="btn btn-primary rounded-l-none">
                  Subscribe
                </button>
              </form>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white">
          <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-lg font-semibold mb-4">CryptoAnalytics</h3>
                <p className="text-gray-400">
                  Advanced cryptocurrency trading signal analysis platform.
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="#features" className="hover:text-white">Features</Link></li>
                  <li><Link href="#pricing" className="hover:text-white">Pricing</Link></li>
                  <li><Link href="/docs" className="hover:text-white">Documentation</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/about" className="hover:text-white">About</Link></li>
                  <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                  <li><Link href="/privacy" className="hover:text-white">Privacy</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-4">Support</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/help" className="hover:text-white">Help Center</Link></li>
                  <li><Link href="/contact" className="hover:text-white">Contact Support</Link></li>
                  <li><Link href="/status" className="hover:text-white">Status</Link></li>
                </ul>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400">
              <p>&copy; 2024 CryptoAnalytics. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
} 