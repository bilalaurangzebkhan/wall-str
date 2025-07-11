import ThemeSwitcher from "@/components/ThemeSwitcher";

export default function Footer() {
  return (
    <footer className="py-4 md:py-0 text-center text-xs text-base-content/60 bg-base-200">
      <ThemeSwitcher />
    </footer>
  );
}
