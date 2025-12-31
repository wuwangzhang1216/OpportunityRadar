"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/auth-store";

const signupSchema = z
  .object({
    fullName: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type SignupForm = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading, error, clearError } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupForm>({
    resolver: zodResolver(signupSchema),
  });

  const onSubmit = async (data: SignupForm) => {
    try {
      await signup(data.email, data.password, data.fullName);
      router.push("/profile");
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-center mb-2">Create an account</h1>
      <p className="text-gray-600 text-center mb-8">
        Start discovering opportunities today
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-1">Full Name</label>
          <Input
            type="text"
            placeholder="John Doe"
            {...register("fullName")}
            onFocus={() => clearError()}
          />
          {errors.fullName && (
            <p className="text-red-500 text-sm mt-1">
              {errors.fullName.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <Input
            type="email"
            placeholder="you@example.com"
            {...register("email")}
            onFocus={() => clearError()}
          />
          {errors.email && (
            <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <Input
            type="password"
            placeholder="At least 8 characters"
            {...register("password")}
            onFocus={() => clearError()}
          />
          {errors.password && (
            <p className="text-red-500 text-sm mt-1">
              {errors.password.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Confirm Password
          </label>
          <Input
            type="password"
            placeholder="Confirm your password"
            {...register("confirmPassword")}
            onFocus={() => clearError()}
          />
          {errors.confirmPassword && (
            <p className="text-red-500 text-sm mt-1">
              {errors.confirmPassword.message}
            </p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Creating account..." : "Create account"}
        </Button>
      </form>

      <p className="text-center mt-6 text-gray-600">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-600 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
