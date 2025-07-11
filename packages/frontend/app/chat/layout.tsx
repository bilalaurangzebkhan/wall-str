import Footer from "@/components/footer/Footer";
import Header from "@/components/header/Header";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen max-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex overflow-y-auto">{children}</main>
      <Footer />
    </div>
  );
}
