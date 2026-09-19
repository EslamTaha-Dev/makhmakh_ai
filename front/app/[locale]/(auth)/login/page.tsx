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
import { useQueryParam } from "@/hooks/use-query-param";
import { Link, useRouter } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/** Only relative app paths are honoured, so `next` cannot become an open redirect. */
function isSafeInternalPath(value: string | null): value is string {
  return Boolean(value) && value!.startsWith("/") && !value!.startsWith("//");
}

export default function LoginPage() {
  const t = useTranslations("auth.login");
  const tValidation = useTranslations("validation");
  const router = useRouter();
  const describeError = useApiErrorMessage();
  const signIn = useSessionStore((state) => state.signIn);
  // The app shell sends guests here with the page they wanted.
  const { value: nextPath } = useQueryParam("next");
  const { value: reason } = useQueryParam("reason");

  const schema = z.object({
    email: z
      .string()
      .min(1, tValidation("required"))
      .regex(EMAIL_PATTERN, tValidation("email")),
    password: z.string().min(1, tValidation("required")),
  });

  type FormValues = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const user = await signIn(values.email, values.password);
      toast.success(t("submit"), { description: user.name });
      router.replace(isSafeInternalPath(nextPath) ? nextPath : "/dashboard");
    } catch (error) {
      setError("root", {
        message: describeError(error, "login"),
      });
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

      {reason === "session-expired" ? (
        <Alert tone="warning">{t("sessionExpired")}</Alert>
      ) : null}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
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
            placeholder={t("placeholderEmail")}
            aria-invalid={Boolean(errors.email)}
            {...register("email")}
          />
        </Field>

        <Field
          label={t("password")}
          htmlFor="password"
          required
          error={errors.password?.message}
        >
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder={t("placeholderPassword")}
            aria-invalid={Boolean(errors.password)}
            {...register("password")}
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

      <p className="text-center text-sm text-muted-fg">
        {t("noAccount")}{" "}
        <Link
          href="/register"
          className="font-medium text-brand-600 hover:underline"
        >
          {t("createAccount")}
        </Link>
      </p>
    </div>
  );
}
