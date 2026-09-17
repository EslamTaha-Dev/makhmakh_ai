"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { useCreateCourse } from "@/hooks/use-courses";
import { useRouter } from "@/i18n/routing";
import type { Course } from "@/lib/api/types";
import { cn } from "@/lib/utils";

type CreateSpaceDialogProps = {
  /** Rendered instead of the default trigger when provided. */
  trigger?: React.ReactNode;
  className?: string;
  /** Navigate to the new space once it exists. */
  navigateOnCreate?: boolean;
  onCreated?: (course: Course) => void;
};

export function CreateSpaceDialog({
  trigger,
  className,
  navigateOnCreate = false,
  onCreated,
}: CreateSpaceDialogProps) {
  const t = useTranslations("subjects.create");
  const tValidation = useTranslations("validation");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const describeError = useApiErrorMessage();
  const createCourse = useCreateCourse();

  const [open, setOpen] = React.useState(false);

  const schema = z.object({
    name: z.string().trim().min(2, tValidation("nameMin")),
    description: z.string().trim().max(500).optional(),
  });

  type FormValues = z.infer<typeof schema>;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", description: "" },
  });

  const onSubmit = async (values: FormValues) => {
    try {
      const course = await createCourse.mutateAsync({
        name: values.name,
        description: values.description?.trim() ? values.description : null,
        price: 0,
      });

      toast.success(t("success"), { description: course.name });
      setOpen(false);
      reset();
      onCreated?.(course);

      if (navigateOnCreate) {
        router.push(`/subjects/${course.id}`);
      }
    } catch (error) {
      toast.error(describeError(error, "generic"));
    }
  };

  return (
    <>
      {trigger ? (
        <span onClick={() => setOpen(true)} className={cn("contents", className)}>
          {trigger}
        </span>
      ) : (
        <Button onClick={() => setOpen(true)} className={className}>
          <Plus aria-hidden />
          {t("submit")}
        </Button>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={t("title")}
        description={t("subtitle")}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
          <Field
            label={t("name")}
            htmlFor="space-name"
            required
            error={errors.name?.message}
          >
            <Input
              id="space-name"
              placeholder={t("placeholderName")}
              aria-invalid={Boolean(errors.name)}
              {...register("name")}
            />
          </Field>

          <Field
            label={t("description")}
            htmlFor="space-description"
            error={errors.description?.message}
          >
            <Textarea
              id="space-description"
              placeholder={t("placeholderDescription")}
              {...register("description")}
            />
          </Field>

          <Alert tone="info">{tCommon("appNameLatin")} — {t("subtitle")}</Alert>

          <div className="flex flex-wrap justify-end gap-3">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              {tCommon("cancel")}
            </Button>

            <Button
              type="submit"
              loading={isSubmitting}
              loadingText={t("submitting")}
            >
              {t("submit")}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
