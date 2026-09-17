"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { Link, useRouter } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export default function RegisterPage() {
  const t = useTranslations("auth.register");
  const tValidation = useTranslations("validation");
  const router = useRouter();
  const describeError = useApiErrorMessage();
  const signUp = useSessionStore((state) => state.signUp);

  const schema = z
    .object({
      name: z.string().trim().min(2, tValidation("nameMin")),
      email: z
        .string()
        .min(1, tValidation("required"))
        .regex(EMAIL_PATTERN, tValidation("email")),
      password: z.string().min(8, tValidation("passwordMin")),
      confirmPassword: z.string().min(1, tValidation("required")),
    })
    .refine((values) => values.password === values.confirmPassword, {
      path: ["confirmPassword"],
      message: tValidation("passwordMismatch"),
    });

  type FormValues = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      await signUp(values.name, values.email, values.password);
      toast.success(t("title"), { description: values.email });
      router.replace("/dashboard");
    } catch (error) {
      setError("root", { message: describeError(error, "register") });
    }
  };

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
      </header>

      {errors.root?.message ? (
        <Alert tone="error">{errors.root.message}</Alert>
      ) : null}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <Field
          label={t("name")}
          htmlFor="name"
          required
          error={errors.name?.message}
        >
          <Input
            id="name"
            autoComplete="name"
            placeholder={t("placeholderName")}
            aria-invalid={Boolean(errors.name)}
            {...register("name")}
          />
        </Field>

        <Field
          label={t("email")}
          htmlFor="email"
          required
          error={errors.email?.message}
        >
          <Input
            id="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            dir="ltr"
            placeholder="name@example.com"
            aria-invalid={Boolean(errors.email)}
            {...register("email")}
          />
        </Field>

        <Field
          label={t("password")}
          htmlFor="password"
          required
          hint={t("passwordHint")}
          error={errors.password?.message}
        >
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            aria-invalid={Boolean(errors.password)}
            {...register("password")}
          />
        </Field>

        <Field
          label={t("confirmPassword")}
          htmlFor="confirmPassword"
          required
          error={errors.confirmPassword?.message}
        >
          <Input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            aria-invalid={Boolean(errors.confirmPassword)}
            {...register("confirmPassword")}
          />
        </Field>

        <Button
          type="submit"
          size="lg"
          block
          loading={isSubmitting}
          loadingText={t("submitting")}
        >
          {t("submit")}
        </Button>

        <p className="text-center text-xs text-muted-fg break-arabic">
          {t("terms")}
        </p>
      </form>

      <p className="text-center text-sm text-muted-fg">
        {t("hasAccount")}{" "}
        <Link href="/login" className="font-medium text-brand-600 hover:underline">
          {t("signIn")}
        </Link>
      </p>
    </div>
  );
}
