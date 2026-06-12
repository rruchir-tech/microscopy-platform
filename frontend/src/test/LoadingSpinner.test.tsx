import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LoadingSpinner } from "@/components/Shared/LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders the default label", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders a custom label", () => {
    render(<LoadingSpinner label="Fetching data" />);
    expect(screen.getByText("Fetching data")).toBeInTheDocument();
  });
});
