"use client";
import { useCallback, useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import { api } from "@/api";
import { setToken } from "@/utils/auth";

type SignInFormData = {
  email: string;
  password: string;
};

export default function SignInForm({
  urls,
  authProviders,
  allowSignup,
}: {
  urls: { forgotPassword: string; signUp: string };
  authProviders: string[];
  allowSignup: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting },
  } = useForm<SignInFormData>();

  const onSubmit = useCallback(
    async (data: SignInFormData) => {
      setError(null);
      const { data: accessToken, response } = await api.auth.signin({ body: data, credentials: "include" });

      if (!accessToken) {
        if (response.status === 401) {
          setError("Incorrect email or password");
          return;
        }
        setError("Something went wrong");
        return;
      }

      setToken(accessToken.token);
      router.push("/chat");
    },
    [router],
  );

  return (
    <div>
      <h2 className="text-2xl font-bold text-center">Sign In</h2>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="alert alert-error mt-2">
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-1">
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            className={`input w-full ${errors.email ? "input-error" : ""}`}
            id="email"
            type="email"
            {...register("email", {
              required: "Email is required",
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: "Invalid email address",
              },
            })}
            placeholder="Enter your email"
          />
          {errors.email && <span className="text-error text-sm">{errors.email.message}</span>}
        </div>

        <div className="space-y-1">
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            className={`input w-full ${errors.password ? "input-error" : ""}`}
            id="password"
            type="password"
            {...register("password", {
              required: "Password is required",
            })}
            placeholder="Enter your password"
          />
          {errors.password && <span className="text-error text-sm">{errors.password.message}</span>}
          {/* Disable until implemented
          <div className="text-sm text-right">
            <a href={urls.forgotPassword} className="label link link-hover">
              Forgot password?
            </a>
          </div>
          */}
        </div>

        <button type="submit" className="btn btn-neutral w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing In..." : "Sign In"}
        </button>
        {authProviders.length > 0 ? (
          <>
            <div className="divider">or sign in with</div>

            <div className="flex flex-col space-y-2">
              {authProviders.includes("google") && (
                <button className="btn btn-outline w-full" disabled>
                  Sign in with Google
                </button>
              )}

              {authProviders.includes("github") && (
                <button className="btn btn-outline w-full" disabled>
                  Sign in with GitHub
                </button>
              )}
            </div>
          </>
        ) : null}

        <p className="text-sm text-center text-gray-600">
          Don&apos;t have an account?{" "}
          {allowSignup ? (
            <a href={urls.signUp} className="link link-primary">
              Sign up here
            </a>
          ) : (
            <a href="mailto:team@wallstr.chat" className="link link-primary">
              Message to us
            </a>
          )}
        </p>
      </form>
    </div>
  );
}
