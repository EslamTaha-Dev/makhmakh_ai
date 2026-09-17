/**
 * Upload contract.
 *
 * Kept in sync with `back/app/api/routes/materials.py` (ALLOWED_EXTENSIONS) and the
 * `UPLOAD_MAX_SIZE_MB` backend setting.
 */
export const ACCEPTED_UPLOAD_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".pptx",
  ".ppt",
  ".txt",
  ".mp3",
  ".wav",
  ".mp4",
  ".mov",
] as const;

export const UPLOAD_ACCEPT_ATTR = ACCEPTED_UPLOAD_EXTENSIONS.join(",");

export const UPLOAD_MAX_SIZE_MB = Number(
  process.env.NEXT_PUBLIC_UPLOAD_MAX_SIZE_MB ?? 100,
);

export const UPLOAD_MAX_SIZE_BYTES = UPLOAD_MAX_SIZE_MB * 1024 * 1024;

export function isAcceptedUpload(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return ACCEPTED_UPLOAD_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/** Human label for a material's file type, used in lists. */
export const FILE_TYPE_LABEL: Record<string, string> = {
  pdf: "PDF",
  docx: "Word",
  pptx: "PowerPoint",
  ppt: "PowerPoint",
  txt: "Text",
  mp3: "MP3",
  wav: "WAV",
  mp4: "MP4",
  mov: "MOV",
};
