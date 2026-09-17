"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { Link } from "@/i18n/routing";
import * as api from "@/lib/api/endpoints";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export default function ForgotPasswordPage() {
  const t = useTranslations("auth.forgot");
  const tValidation = useTranslations("validation");
  const describeError = useApiErrorMessage();

  const [sent, setSent] = React.useState(false);
  const [devToken, setDevToken] = React.useState<string | null>(null);

  const schema = z.object({
    email: z
      .string()
      .min(1, tValidation("required"))
      .regex(EMAIL_PATTERN, tValidation("email")),
  });

  type FormValues = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const result = await api.forgotPassword({ email: values.email });
      setDevToken(result.reset_token ?? null);
      setSent(true);
    } catch (error) {
      setError("root", { message: describeError(error, "forgot") });
    }
  };

  if (sent) {
    return (
      <div className="space-y-6">
        <header className="space-y-2">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("sentTitle")}
          </h1>
          <p className="text-sm text-muted-fg break-arabic">{t("sentBody")}</p>
        </header>

        {devToken ? (
          <Alert tone="warning" title={t("devTokenTitle")}>
            <p className="mb-3 break-arabic">{t("devTokenBody")}</p>
            <Link
              href={{ pathname: "/reset-password", query: { token: devToken } }}
              className="font-medium text-brand-700 underline"
            >
              {t("useDevToken")}
            </Link>
          </Alert>
        ) : null}

        <Link
          href="/login"
          className="inline-block text-sm font-medium text-brand-600 hover:underline"
        >
          {t("backToLogin")}
        </Link>
      </div>
    );
  }

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
          label={t("title")}
          htmlFor="email"
          required
          error={errors.email?.message}
          className="[&>label]:sr-only"
        >
          <Input
            id="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            dir="ltr"
            placeholder="name@example.com"
            aria-invalid={Boolean(errors.email)}
            aria-label={t("title")}
            {...register("email")}
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
      </form>

      <Link
        href="/login"
        className="block text-center text-sm font-medium text-brand-600 hover:underline"
      >
        {t("backToLogin")}
      </Link>
    </div>
  );
}
