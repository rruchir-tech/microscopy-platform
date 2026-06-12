import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/store/authStore";

describe("authStore", () => {
  beforeEach(() => useAuthStore.getState().logout());

  it("starts unauthenticated", () => {
    expect(useAuthStore.getState().isAuthenticated()).toBe(false);
  });

  it("stores tokens and reports authenticated", () => {
    useAuthStore.getState().setTokens("access-1", "refresh-1");
    expect(useAuthStore.getState().accessToken).toBe("access-1");
    expect(useAuthStore.getState().isAuthenticated()).toBe(true);
  });

  it("logout clears everything", () => {
    useAuthStore.getState().setTokens("a", "b");
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});
