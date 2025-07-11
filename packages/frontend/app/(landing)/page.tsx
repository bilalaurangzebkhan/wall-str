"use client";
import { AgGridReact } from "ag-grid-react";
import {
  ClientSideRowModelModule,
  CellStyleModule,
  RowAutoHeightModule,
  ColDef,
  colorSchemeDarkBlue,
  themeAlpine,
} from "ag-grid-community";
import { useRouter } from "next/navigation";
import Image from "next/image";

import Navbar from "./_components/Navbar";
import Footer from "./_components/Footer";
import {
  AnthropicSVG,
  AzureSVG,
  ClaudeSVG,
  DeepSeekSVG,
  GeminiSVG,
  GemmaSVG,
  GoogleSVG,
  HuggingFaceSVG,
  MetaSVG,
  OllamaSVG,
  OpenAISVG,
  ReplicateSVG,
} from "./_components/icons";

import type { ReactNode } from "react";

const FeatureIcons = {
  analysis: (
    <svg className="w-12 h-12 mb-4" viewBox="0 0 24 24">
      <defs>
        <linearGradient id="metallic-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#D4D4D4">
            <animate attributeName="stop-color" values="#D4D4D4;#2C2C2C;#D4D4D4" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="50%" stopColor="#8E8E8E">
            <animate attributeName="stop-color" values="#8E8E8E;#515151;#8E8E8E" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="100%" stopColor="#2C2C2C">
            <animate attributeName="stop-color" values="#2C2C2C;#D4D4D4;#2C2C2C" dur="3s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
      </defs>

      <g
        stroke="url(#metallic-gradient)"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.2}
        fill="none"
        transform="scale(0.7)"
      >
        <path d="M21,21L21,21   c1.105-1.105,2.895-1.105,4,0l5.172,5.172c0.53,0.53,0.828,1.25,0.828,2v0C31,29.734,29.734,31,28.172,31h0   c-0.75,0-1.47-0.298-2-0.828L21,25C19.895,23.895,19.895,22.105,21,21z" />
        <circle cx="11" cy="11" r="10" />
        <path d="M11,5 c-3.314,0-6,2.686-6,6" />
        <line x1="18" x2="21" y1="18" y2="21" />
      </g>
    </svg>
  ),
  memos: (
    <svg className="w-12 h-12 mb-4" viewBox="0 0 24 24">
      <defs>
        <linearGradient id="metallic-gradient-2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#D4D4D4">
            <animate attributeName="stop-color" values="#D4D4D4;#2C2C2C;#D4D4D4" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="50%" stopColor="#8E8E8E">
            <animate attributeName="stop-color" values="#8E8E8E;#515151;#8E8E8E" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="100%" stopColor="#2C2C2C">
            <animate attributeName="stop-color" values="#2C2C2C;#D4D4D4;#2C2C2C" dur="3s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
      </defs>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1}
        stroke="url(#metallic-gradient-2)"
        fill="none"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  ),
  security: (
    <svg className="w-12 h-12 mb-4" viewBox="0 0 24 24">
      <defs>
        <linearGradient id="metallic-gradient-3" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#D4D4D4">
            <animate attributeName="stop-color" values="#D4D4D4;#2C2C2C;#D4D4D4" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="50%" stopColor="#8E8E8E">
            <animate attributeName="stop-color" values="#8E8E8E;#515151;#8E8E8E" dur="3s" repeatCount="indefinite" />
          </stop>
          <stop offset="100%" stopColor="#2C2C2C">
            <animate attributeName="stop-color" values="#2C2C2C;#D4D4D4;#2C2C2C" dur="3s" repeatCount="indefinite" />
          </stop>
        </linearGradient>
      </defs>

      <g stroke="url(#metallic-gradient-3)" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} fill="none">
        <path d="M12.0001 7.88989L10.9301 9.74989C10.6901 10.1599 10.8901 10.4999 11.3601 10.4999H12.6301C13.1101 10.4999 13.3001 10.8399 13.0601 11.2499L12.0001 13.1099" />
        <path d="M8.30011 18.0399V16.8799C6.00011 15.4899 4.11011 12.7799 4.11011 9.89993C4.11011 4.94993 8.66011 1.06993 13.8001 2.18993C16.0601 2.68993 18.0401 4.18993 19.0701 6.25993C21.1601 10.4599 18.9601 14.9199 15.7301 16.8699V18.0299C15.7301 18.3199 15.8401 18.9899 14.7701 18.9899H9.26011C8.16011 18.9999 8.30011 18.5699 8.30011 18.0399Z" />
        <path d="M8.5 22C10.79 21.35 13.21 21.35 15.5 22" />
      </g>
    </svg>
  ),
};

type TExampleQuery = {
  step: string;
  question: string;
  insight: string;
  source: string;
};

const examples = [
  {
    step: "📊 Business Model",
    question: "What is Company X's core revenue driver, and how has it evolved?",
    insight:
      "Company X generates 75% of revenue from recurring SaaS contracts, transitioning from a licensing model over five years. LTV increased from $18K to $24K per client, while gross margins expanded from 52% to 58%.",
    source: "10-K, Earnings Calls, Investor Presentations",
  },
  {
    step: "💰 Financial Performance",
    question: "How does inflation impact Company X's cost structure?",
    insight:
      "Input costs increased 7% YoY, driven by rising supply chain expenses and labor costs. However, Company X offset inflation through price adjustments and efficiency gains, maintaining an operating margin of 24.5%, compared to 23.8% a year prior.",
    source: "SEC Filings, Analyst Coverage Reports",
  },
  {
    step: "🏆 Competitive Positioning",
    question: "How does Company X defend market share from new entrants?",
    insight:
      "Company X maintains a 32% market share, leveraging strong network effects and switching costs. Over 60% of customers integrate Company X's platform across multiple business units, making replacement costly and inefficient.",
    source: "Competitor 10-Ks, Market Research, Earnings Call Q&A",
  },
  {
    step: "🌎 Market Expansion",
    question: "What is the upside potential of Company X's international expansion?",
    insight:
      "Company X is expanding into [New Market], a $12B opportunity growing at 14% CAGR. Regulatory approvals were recently secured, and initial pilot projects indicate a 20%+ market penetration rate within five years.",
    source: "Investor Presentations, Earnings Calls, Market Research Reports",
  },
  {
    step: "⚠ Risk Factors",
    question: "What regulatory risks could impact Company X's operations?",
    insight:
      "New data privacy laws in [Region] could increase compliance costs by $50M annually, impacting EBITDA margins by 0.6 percentage points. However, Company X has already begun adapting its data architecture to mitigate long-term risk.",
    source: "10-K (Risk Section), Legal Filings, Regulatory Disclosures",
  },
];

const columnDefs: ColDef<TExampleQuery>[] = [
  {
    headerName: "Section",
    field: "step",
    width: 220,
    flex: 1,
    cellStyle: (params) => ({
      padding: "10px",
      fontSize: "13px",
      lineHeight: 1.5,
      alignItems: "center",
      backgroundColor: (params.node.rowIndex ?? 0) % 2 === 0 ? "#151a28" : "#1a1f2f",
    }),
  },
  {
    headerName: "Question",
    field: "question",
    flex: 1.5,
    cellStyle: (params) => ({
      padding: "10px",
      fontSize: "13px",
      lineHeight: 1.5,
      backgroundColor: (params.node.rowIndex ?? 0) % 2 === 0 ? "#151a28" : "#1a1f2f",
    }),
  },
  {
    headerName: "Answer",
    field: "insight",
    flex: 2.5,
    cellStyle: (params) => ({
      padding: "10px",
      fontSize: "13px",
      lineHeight: 1.5,
      backgroundColor: (params.node.rowIndex ?? 0) % 2 === 0 ? "#151a28" : "#1a1f2f",
    }),
  },
  {
    headerName: "Sources",
    field: "source",
    flex: 1,
    cellStyle: (params) => ({
      padding: "10px",
      fontSize: "12px",
      color: "#60a5fa",
      lineHeight: 1.5,
      textDecoration: "underline",
      backgroundColor: (params.node.rowIndex ?? 0) % 2 === 0 ? "#151a28" : "#1a1f2f",
    }),
  },
];

const titleClassName =
  "drop-shadow-lg bg-gradient-to-r bg-[200%_auto] bg-clip-text text-transparent from-white via-slate-400 to-neutral-500";
const subtitleClassName = "drop-shadow-lg bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent";

export default function LandingPage() {
  const router = useRouter();

  return (
    <div
      className={`
      min-h-screen font-sans bg-neutral-950
      text-white
      bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))]
      snap-y snap-proximity`}
    >
      <section id="hero" className="snap-start h-screen flex flex-col text-center">
        <Navbar />
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="max-w-6xl mx-auto">
            <h1 className={`text-5xl md:text-6xl font-bold mb-6 drop-shadow-lg ${titleClassName}`}>
              Transform Hours of Research into Minutes
            </h1>
            <p className="text-xl text-white/80 max-w-3xl mx-auto mb-12">
              Institutional-grade AI analysis trusted by Street investment bankers
            </p>
            <a
              href="mailto:team@wallstr.chat?subject=Demo%20Request&body=Hello,%20I%20would%20like%20to%20book%20a%20demo."
              className="relative inline-block overflow-hidden rounded-2xl p-[1px] transition-transform transform hover:scale-105 active:scale-100"
            >
              <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#a9a9a9_0%,#0c0c0c_50%,#a9a9a9_100%)]"></span>
              <span className="relative inline-flex items-center justify-center rounded-2xl bg-neutral-950/95 px-16 py-3 text-lg font-semibold text-white backdrop-blur-xl hover:bg-black transition-colors">
                Book a Demo
              </span>
            </a>
            <br />
          </div>
        </div>
      </section>

      <section id="features" className="snap-start h-screen relative flex items-center justify-center overflow-hidden">
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1/2 h-3/4 hidden md:block rounded-xl overflow-hidden">
          <div className="relative w-full h-full">
            <Image
              src="/hero.jpg"
              className="opacity-30 object-[75%_0%] object-cover"
              fill
              priority
              alt="Wallstr.chat AI-Powered Research"
            />
            <div className="absolute inset-0 bg-gradient-to-l from-transparent to-neutral-950"></div>
          </div>
        </div>

        <div className="relative z-10 px-8 w-full max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center gap-16">
            <div className="flex-1">
              <h2 className="text-5xl font-bold mb-8 bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent text-center md:text-left">
                Why Choose Wallstr.chat?
              </h2>

              <div className="space-y-8">
                {[
                  {
                    title: "AI-Powered Document Analysis",
                    icon: FeatureIcons.analysis,
                    description: "Secure AI-driven insights with local data storage.",
                  },
                  {
                    title: "Professional Investment Guidance",
                    icon: FeatureIcons.memos,
                    description: "Every response is sourced and data-backed.",
                  },
                  {
                    title: "Clear & Structured Insights",
                    icon: FeatureIcons.security,
                    description: "Precision and transparency in every answer.",
                  },
                ].map((feature, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-6 group p-6 rounded-2xl transition-colors hover:bg-white/5"
                  >
                    <div className="flex-shrink-0 p-3 transition-colors">{feature.icon}</div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2 text-white/90">{feature.title}</h3>
                      <p className="text-white/60 leading-relaxed">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="hidden md:block w-1/3">{/* Spacer for image */}</div>
          </div>
        </div>
      </section>

      <section id="demo" className="snap-start h-screen flex flex-col items-center justify-center px-4 text-center">
        <h2 className={`text-5xl font-bold mb-12 ${titleClassName}`}>Take a look at our demo</h2>
        <div className="relative h-96 md:h-108 w-full md:w-[52.2em] mx-auto overflow-hidden rounded-lg">
          <iframe
            src="https://www.loom.com/embed/6614feff88264d48b488118224a8cf82?sid=1eaf707d-f6ec-4852-8091-5996c3c590b3"
            allowFullScreen={true}
            className="absolute top-0 left-0 w-full h-full border-0"
          ></iframe>
        </div>
      </section>

      <section id="equity-research" className="snap-start h-screen flex items-center px-4 bg-[#0b0f19]">
        <div className="max-w-7xl mx-auto bg-[#10131a] p-8 mt-8 rounded-2xl border border-[#2e323f] shadow-2xl">
          <h2 className={`text-4xl font-bold text-center mb-6 ${titleClassName}`}>AI-Powered Equity Research</h2>
          <p className="text-center text-lg text-gray-400 mb-8">
            Unlike generic AI models, our system builds a custom knowledge base for each company, ensuring deep,
            verifiable insights tailored to your research.
          </p>

          <div
            className="rounded-lg shadow-lg overflow-hidden border border-[#2e323f] bg-[#0a0f1d]"
            style={{ height: 500, width: "100%" }}
          >
            <AgGridReact
              rowData={examples}
              columnDefs={columnDefs}
              modules={[ClientSideRowModelModule, CellStyleModule, RowAutoHeightModule]}
              theme={themeAlpine.withPart(colorSchemeDarkBlue)}
              domLayout="normal"
              pagination={true}
              paginationPageSize={5}
              rowHeight={100}
              suppressRowHoverHighlight={false}
              gridOptions={{
                headerHeight: 50,
              }}
              defaultColDef={{
                autoHeight: true,
                wrapText: true,
                resizable: true,
                sortable: true,
                filter: true,
                minWidth: 140,
              }}
            />
          </div>
        </div>
      </section>

      <section
        id="integrations"
        className="snap-start h-screen flex flex-col items-center justify-center px-4 relative overflow-hidden"
      >
        <div className="max-w-7xl w-full mx-auto space-y-24">
          <div className="space-y-16">
            <h2 className={`text-4xl font-bold text-center ${subtitleClassName}`}>LLM Agnostic</h2>
            <div className="relative w-full overflow-hidden">
              <div className="flex animate-infinite-scroll">
                <div className="flex space-x-24 md:space-x-36">
                  {[
                    { name: "GPT", icon: <OpenAISVG /> },
                    { name: "Claude", icon: <ClaudeSVG /> },
                    { name: "Llama", icon: <MetaSVG /> },
                    { name: "Gemini", icon: <GeminiSVG /> },
                    { name: "Gemma", icon: <GemmaSVG /> },
                    { name: "Deepseek", icon: <DeepSeekSVG /> },
                  ].map((llm, index) => (
                    <GrayscaleIcon title={llm.name} key={index}>
                      {llm.icon}
                    </GrayscaleIcon>
                  ))}
                  {[
                    { name: "GPT", icon: <OpenAISVG /> },
                    { name: "Claude", icon: <ClaudeSVG /> },
                    { name: "Llama", icon: <MetaSVG /> },
                    { name: "Gemini", icon: <GeminiSVG /> },
                    { name: "Gemma", icon: <GemmaSVG /> },
                    { name: "Deepseek", icon: <DeepSeekSVG /> },
                  ].map((llm, index) => (
                    <GrayscaleIcon title={llm.name} key={`dup-${index}`}>
                      {llm.icon}
                    </GrayscaleIcon>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-16">
            <h2 className={`text-4xl font-bold text-center ${subtitleClassName}`}>Provider Agnostic</h2>
            <div className="relative w-full overflow-hidden">
              <div className="flex animate-infinite-scroll-reverse">
                <div className="flex space-x-24 md:space-x-36">
                  {[
                    { name: "Anthropic", icon: <AnthropicSVG /> },
                    { name: "Replicate", icon: <ReplicateSVG /> },
                    { name: "HuggingFace", icon: <HuggingFaceSVG /> },
                    { name: "Ollama", icon: <OllamaSVG /> },
                    { name: "Google Cloud", icon: <GoogleSVG /> },
                    { name: "Azure", icon: <AzureSVG /> },
                    { name: "OpenAI", icon: <OpenAISVG /> },
                  ].map((provider, index) => (
                    <GrayscaleIcon title={provider.name} key={index}>
                      {provider.icon}
                    </GrayscaleIcon>
                  ))}
                  {[
                    { name: "Anthropic", icon: <AnthropicSVG /> },
                    { name: "Replicate", icon: <ReplicateSVG /> },
                    { name: "HuggingFace", icon: <HuggingFaceSVG /> },
                    { name: "Ollama", icon: <OllamaSVG /> },
                    { name: "Google Cloud", icon: <GoogleSVG /> },
                    { name: "Azure", icon: <AzureSVG /> },
                    { name: "OpenAI", icon: <OpenAISVG /> },
                  ].map((provider, index) => (
                    <GrayscaleIcon title={provider.name} key={`dup-${index}`}>
                      {provider.icon}
                    </GrayscaleIcon>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="cta" className="snap-start pt-24 h-screen text-center text-white flex flex-col">
        <div className="max-w-4xl mx-auto px-4 md:px-0 flex-1 flex flex-col items-center justify-center">
          <div className="pb-24">
            <h2 className={`text-4xl font-bold mb-6 ${titleClassName}`}>Start Your AI-Powered Research Today</h2>
            <p className="text-lg text-white/80 max-w-3xl mx-auto mb-8">
              Join Street&apos;s funds accelerating their due diligence with Wallstr.chat
            </p>
            <button
              className="relative inline-block overflow-hidden rounded-2xl p-[1px] transition-transform transform hover:scale-105 active:scale-100 cursor-pointer"
              onClick={() => router.push("/auth/signup")}
            >
              <span className="absolute inset-[-1000%] animate-[spin_2s_linear_infinite] bg-[conic-gradient(from_90deg_at_50%_50%,#a9a9a9_0%,#0c0c0c_50%,#a9a9a9_100%)]"></span>
              <span className="relative inline-flex items-center justify-center rounded-2xl bg-neutral-950/95 w-64 px-16 py-2 text-md font-semibold text-white backdrop-blur-xl active:bg-black transition-colors">
                Sign Up
              </span>
            </button>
          </div>
        </div>
        <Footer />
      </section>
    </div>
  );
}

function GrayscaleIcon({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex flex-col items-center">
      <div className="w-16 h-16 relative text-gray-500 grayscale hover:grayscale-0 hover:text-white transition-all duration-300">
        {children}
      </div>
      <span className="mt-2 text-sm text-center text-white/60 group-hover:text-white/90 transition-colors">
        {title}
      </span>
    </div>
  );
}
