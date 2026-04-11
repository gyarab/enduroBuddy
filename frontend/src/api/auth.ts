import { apiClient } from "@/api/client";

export type AuthMeResponse = {
  id: number;
  full_name: string;
  email: string;
  role: "COACH" | "ATHLETE";
  initials: string;
  capabilities: {
    can_view_coach: boolean;
    can_view_athlete: boolean;
    can_complete_profile: boolean;
    has_garmin_connection: boolean;
    garmin_connect_enabled: boolean;
    garmin_sync_enabled: boolean;
    coached_athlete_count: number;
  };
  default_app_route: string;
};

export async function fetchCurrentUser() {
  const response = await apiClient.get<AuthMeResponse>("/auth/me/");
  return response.data;
}

export type LoginPayload = {
  email: string;
  password: string;
  remember: boolean;
};

export type SignupPayload = {
  first_name: string;
  last_name: string;
  email: string;
  role: "COACH" | "ATHLETE";
  password: string;
  password_confirmation: string;
};

export type AuthActionResponse = {
  ok: boolean;
  message: string;
  redirect_to: string;
  errors?: Record<string, string[]>;
};

export async function loginWithPassword(payload: LoginPayload) {
  const response = await apiClient.post<AuthActionResponse>("/auth/login/", payload);
  return response.data;
}

export async function signupWithPassword(payload: SignupPayload) {
  const response = await apiClient.post<AuthActionResponse>("/auth/signup/", payload);
  return response.data;
}

export async function requestPasswordReset(email: string) {
  const response = await apiClient.post<AuthActionResponse>("/auth/password/reset/", { email });
  return response.data;
}

export async function logoutFromSession() {
  const response = await apiClient.post<AuthActionResponse>("/auth/logout/");
  return response.data;
}

export type EmailConfirmState = {
  ok: boolean;
  can_confirm: boolean;
  email?: string;
  user?: {
    display: string;
  };
  message?: string;
};

export type PasswordResetKeyState = {
  ok: boolean;
  token_valid: boolean;
  message?: string;
  redirect_to?: string;
};

export type EmailAddressItem = {
  email: string;
  verified: boolean;
  primary: boolean;
  can_delete: boolean;
  can_mark_primary: boolean;
};

export type EmailAddressesState = {
  ok: boolean;
  emails: EmailAddressItem[];
  can_add_email: boolean;
  current_email: string;
};

export type PasswordSetState = {
  ok: boolean;
  has_usable_password: boolean;
  redirect_to: string;
};

export type SocialConnectionItem = {
  id: number;
  provider: string;
  provider_name: string;
  brand_name: string;
  label: string;
  uid: string;
};

export type SocialConnectionsState = {
  ok: boolean;
  accounts: SocialConnectionItem[];
  connect_google_url: string;
};

export type ReauthenticateState = {
  ok: boolean;
  next: string;
  has_usable_password: boolean;
};

export async function fetchEmailConfirmState(key: string) {
  const response = await apiClient.get<EmailConfirmState>(`/auth/email/confirm/${key}/`);
  return response.data;
}

export async function confirmEmailKey(key: string) {
  const response = await apiClient.post<AuthActionResponse>(`/auth/email/confirm/${key}/`);
  return response.data;
}

export async function fetchPasswordResetKeyState(uidb36: string, key: string) {
  const response = await apiClient.get<PasswordResetKeyState>(`/auth/password/reset/key/${uidb36}-${key}/`);
  return response.data;
}

export async function submitPasswordResetFromKey(uidb36: string, key: string, password: string, passwordConfirmation: string) {
  const response = await apiClient.post<AuthActionResponse>(`/auth/password/reset/key/${uidb36}-${key}/`, {
    password,
    password_confirmation: passwordConfirmation,
  });
  return response.data;
}

export async function fetchEmailAddresses() {
  const response = await apiClient.get<EmailAddressesState>("/auth/email/");
  return response.data;
}

export async function mutateEmailAddress(action: "add" | "primary" | "send" | "remove", payload: { email?: string; new_email?: string }) {
  const response = await apiClient.post<AuthActionResponse & { emails?: EmailAddressItem[] }>("/auth/email/", {
    action,
    ...payload,
  });
  return response.data;
}

export async function changePassword(currentPassword: string, password: string, passwordConfirmation: string) {
  const response = await apiClient.post<AuthActionResponse>("/auth/password/change/", {
    current_password: currentPassword,
    password,
    password_confirmation: passwordConfirmation,
  });
  return response.data;
}

export async function fetchPasswordSetState() {
  const response = await apiClient.get<PasswordSetState>("/auth/password/set/");
  return response.data;
}

export async function setPassword(password: string, passwordConfirmation: string) {
  const response = await apiClient.post<AuthActionResponse>("/auth/password/set/", {
    password,
    password_confirmation: passwordConfirmation,
  });
  return response.data;
}

export async function fetchSocialConnections() {
  const response = await apiClient.get<SocialConnectionsState>("/auth/social/connections/");
  return response.data;
}

export async function disconnectSocialAccount(accountId: number) {
  const response = await apiClient.post<AuthActionResponse & { accounts?: SocialConnectionItem[] }>(
    "/auth/social/connections/",
    { account_id: accountId },
  );
  return response.data;
}

export async function fetchReauthenticateState(next?: string) {
  const response = await apiClient.get<ReauthenticateState>("/auth/reauthenticate/", {
    params: next ? { next } : {},
  });
  return response.data;
}

export async function submitReauthenticate(password: string, next?: string) {
  const response = await apiClient.post<AuthActionResponse>("/auth/reauthenticate/", {
    password,
    next,
  });
  return response.data;
}
