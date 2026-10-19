import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";

const signInMock = vi.fn();
const navigateMock = vi.fn();

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    signIn: signInMock,
    isAuthenticated: false,
    isLoading: false,
    user: null,
  }),
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

vi.mock("@/components/LiquidEther", () => ({
  default: () => <div data-testid="liquid-ether" />,
}));

vi.mock("@/components/ui/card-swap", () => ({
  default: ({ children }: any) => <div>{children}</div>,
  Card: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("@/components/ui/spotlight-card", () => ({
  SpotlightCard: ({ children }: any) => <div>{children}</div>,
}));

import LoginPage from "@/pages/Login";

describe("LoginPage", () => {
  beforeEach(() => {
    signInMock.mockReset();
    navigateMock.mockReset();
  });

  it("renders empty username/password fields", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    expect(screen.getByLabelText(/username or email/i)).toHaveValue("");
    expect(screen.getByLabelText(/password/i)).toHaveValue("");
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Rimini Street" })).toHaveAttribute("src", "/rs_stacked.svg");
  });

  it("submits credentials through signIn", async () => {
    const user = userEvent.setup();
    signInMock.mockResolvedValue({ success: true, message: "ok" });
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/username or email/i), "jane_doe");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => {
      expect(signInMock).toHaveBeenCalledWith("jane_doe", "password123");
    });
  });

  it("shows error when signIn fails", async () => {
    const user = userEvent.setup();
    signInMock.mockResolvedValue({ success: false, message: "bad creds" });
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    await user.type(screen.getByLabelText(/username or email/i), "jane_doe");
    await user.type(screen.getByLabelText(/password/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => expect(signInMock).toHaveBeenCalled());
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it("blocks empty username", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    await user.clear(screen.getByLabelText(/username or email/i));
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(signInMock).not.toHaveBeenCalled();
  });
});
