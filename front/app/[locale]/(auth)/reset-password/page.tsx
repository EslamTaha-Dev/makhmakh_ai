"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2 } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/states";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { useQueryParam } from "@/hooks/use-query-param";
import { Link } from "@/i18n/routing";
import * as api from "@/lib/api/endpoints";

export default function ResetPasswordPage() {
  const t = useTranslations("auth.reset");
  const tValidation = useTranslations("validation");
  const describeError = useApiErrorMessage();

  const { value: token, ready } = useQueryParam("token");
  const [done, setDone] = React.useState(false);

  const schema = z
    .object({
      newPassword: z.string().min(8, tValidation("passwordMin")),
      confirmPassword: z.string().min(1, tValidation("required")),
    })
    .refine((values) => values.newPassword === values.confirmPassword, {
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
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  const onSubmit = async (values: FormValues) => {
    if (!token) {
      setError("root", { message: t("missingToken") });
      return;
    }

    try {
      await api.resetPassword({
        token,
        new_password: values.newPassword,
      });
      setDone(true);
    } catch (error) {
      setError("root", { message: describeError(error, "reset") });
    }
  };

  if (!ready) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (!token) {
    return (
      <div className="space-y-6">
        <Alert tone="error" title={t("title")}>
          {t("missingToken")}
        </Alert>

        <Link
          href="/forgot-password"
          className="inline-block text-sm font-medium text-brand-600 hover:underline"
        >
          {t("submit")}
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="space-y-6">
        <span className="flex size-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
          <CheckCircle2 aria-hidden className="size-7" />
        </span>

        <header className="space-y-2">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("successTitle")}
          </h1>
          <p className="text-sm text-muted-fg break-arabic">{t("successBody")}</p>
        </header>

        <Link
          href="/login"
          className="inline-block text-sm font-medium text-brand-600 hover:underline"
        >
          {t("goToLogin")}
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
          label={t("newPassword")}
          htmlFor="newPassword"
          required
          error={errors.newPassword?.message}
        >
          <Input
            id="newPassword"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            aria-invalid={Boolean(errors.newPassword)}
            {...register("newPassword")}
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
      </form>
    </div>
  );
}
