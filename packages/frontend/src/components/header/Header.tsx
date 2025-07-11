import Link from "next/link";

import UserMenu from "@/components/user/UserMenu";

export default function Header() {
  return (
    <header className="border-b border-base-300 bg-base-100">
      <div className="flex h-16 items-center justify-between px-4">
        <h1 className="text-xl font-semibold">
          <Link href="/">
            <span className="text-2xl">wallstr</span>
            <span className="pl-0.5 text-base-content/60 text-sm">.chat</span>
          </Link>
        </h1>
        <UserMenu />
      </div>
    </header>
  );
}
