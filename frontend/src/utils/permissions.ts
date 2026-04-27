/**
 * Permission helpers for role-based UI rendering.
 */

const ROLE_HIERARCHY: Record<string, number> = {
  member: 0,
  admin: 1,
  owner: 2,
};

export function hasPermission(userRole: string, requiredRole: string): boolean {
  return (ROLE_HIERARCHY[userRole] ?? -1) >= (ROLE_HIERARCHY[requiredRole] ?? 99);
}

export function canManageMembers(role: string): boolean {
  return hasPermission(role, 'admin');
}

export function canChangeRoles(role: string): boolean {
  return hasPermission(role, 'owner');
}

export function canDeleteTasks(role: string): boolean {
  return hasPermission(role, 'admin');
}

export function canInviteMembers(role: string): boolean {
  return hasPermission(role, 'admin');
}
