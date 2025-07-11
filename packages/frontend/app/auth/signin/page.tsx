"use client";
import SignInForm from "@/components/auth/SignInForm";
import { useContext } from "react";

import { ConfigContext } from "@/providers/ConfigProvider";

export default function SignIn() {
  const config = useContext(ConfigContext);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg mx-2 md:mx-0">
        <SignInForm
          urls={{ signUp: "/auth/signup", forgotPassword: "/auth/forgot-password" }}
          authProviders={config?.auth.providers || []}
          allowSignup={config?.auth.allow_signup ?? true}
        />
      </div>
    </div>
  );
}
