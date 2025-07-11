"use client";
import { useCallback, useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import { api } from "@/api";

type SignUpFormData = {
  email: string;
  password: string;
  username: string;
  fullname: string;
};

export default function SignUpForm({ urls, authProviders }: { urls: { signIn: string }; authProviders: string[] }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting },
  } = useForm<SignUpFormData>();

  const onSubmit = useCallback(
    async (data: SignUpFormData) => {
      try {
        setError(null);
        const { response } = await api.auth.signup({
          body: data,
        });

        if (!response.ok) {
          if (response.status === 409) {
            setError("Email already registered");
            return;
          }
          setError("Something went wrong");
          return;
        }

        // Successful signup - redirect to signin
        router.push(urls.signIn);
      } catch {
        setError("Network error. Please try again.");
      }
    },
    [router, urls.signIn],
  );

  return (
    <div>
      <h2 className="text-2xl font-bold text-center">Sign Up</h2>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="alert alert-error">
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
          <label className="label" htmlFor="username">
            Username
          </label>
          <input
            className={`input w-full ${errors.username ? "input-error" : ""}`}
            id="username"
            type="text"
            {...register("username", {
              required: "Username is required",
              pattern: {
                value: /^[a-zA-Z0-9._-]{3,32}$/,
                message: "Username must be 3-32 characters and can only contain letters, numbers, and ._-",
              },
            })}
            placeholder="Choose a username"
          />
          {errors.username && <span className="text-error text-sm">{errors.username.message}</span>}
        </div>

        <div className="space-y-1">
          <label className="label" htmlFor="fullname">
            Full Name
          </label>
          <input
            className={`input w-full ${errors.fullname ? "input-error" : ""}`}
            id="fullname"
            type="text"
            {...register("fullname", {
              required: "Full name is required",
              minLength: {
                value: 2,
                message: "Full name must be at least 2 characters",
              },
              maxLength: {
                value: 128,
                message: "Full name must be less than 128 characters",
              },
            })}
            placeholder="Enter your full name"
          />
          {errors.fullname && <span className="text-error text-sm">{errors.fullname.message}</span>}
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
              minLength: {
                value: 8,
                message: "Password must be at least 8 characters",
              },
            })}
            placeholder="Create a password"
          />
          {errors.password && <span className="text-error text-sm">{errors.password.message}</span>}
        </div>

        <button type="submit" className="btn btn-neutral w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating Account..." : "Create Account"}
        </button>

        {authProviders.length > 0 && (
          <>
            <div className="divider">or sign up with</div>

            <div className="flex flex-col space-y-2">
              {authProviders.includes("google") && (
                <button className="btn btn-outline w-full" disabled>
                  Sign up with Google
                </button>
              )}

              {authProviders.includes("github") && (
                <button className="btn btn-outline w-full" disabled>
                  Sign up with GitHub
                </button>
              )}
            </div>
          </>
        )}

        <p className="text-sm text-center text-gray-600">
          Already have an account?{" "}
          <a href={urls.signIn} className="link link-primary">
            Sign in here
          </a>
        </p>
      </form>
    </div>
  );
}
