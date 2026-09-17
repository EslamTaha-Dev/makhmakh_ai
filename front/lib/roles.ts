/** Account roles supported by the backend, mirrored from the API schema. */
export const roleKeys = [
  "student",
  "instructor",
  "content_creator",
  "support",
  "admin",
  "super_admin",
] as const;

export type RoleKey = (typeof roleKeys)[number];

export function isRoleKey(role: string): role is RoleKey {
  return (roleKeys as readonly string[]).includes(role);
}
