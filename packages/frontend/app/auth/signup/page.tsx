import SignUpForm from "@/components/auth/SignUpForm";
import { api } from "@/api";
import { redirect } from "next/navigation";

export default async function SignUp() {
  const { data: config } = await api.default.getConfig();
  if (config?.auth.allow_signup === false) {
    return redirect("/");
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg mx-2 md:mx-0">
        <SignUpForm urls={{ signIn: "/auth/signin" }} authProviders={config?.auth.providers || []} />
      </div>
    </div>
  );
}
