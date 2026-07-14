"use client";

import { memo, useMemo } from "react";
import { ChevronDown } from "lucide-react";

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

type PageToken = number | "start-ellipsis" | "end-ellipsis";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  itemLabel?: string;
  disabled?: boolean;
  className?: string;
}

function createRange(start: number, end: number) {
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

function getPageTokens(currentPage: number, totalPages: number): PageToken[] {
  const lastPage = Math.max(1, totalPages);
  const activePage = Math.min(Math.max(1, currentPage), lastPage);

  if (lastPage <= 7) {
    return createRange(1, lastPage);
  }

  if (activePage <= 4) {
    return [1, 2, 3, 4, 5, "end-ellipsis", lastPage];
  }

  if (activePage >= lastPage - 3) {
    return [1, "start-ellipsis", ...createRange(lastPage - 4, lastPage)];
  }

  return [
    1,
    "start-ellipsis",
    ...createRange(activePage - 2, activePage + 2),
    "end-ellipsis",
    lastPage,
  ];
}

function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  itemLabel = "items",
  disabled = false,
  className = "",
}: PaginationProps) {
  const lastPage = Math.max(1, totalPages);
  const activePage = Math.min(Math.max(1, currentPage), lastPage);
  const startItem = totalItems === 0 ? 0 : (activePage - 1) * pageSize + 1;
  const endItem = Math.min(activePage * pageSize, totalItems);

  const pageTokens = useMemo(
    () => getPageTokens(activePage, lastPage),
    [activePage, lastPage],
  );

  const goToPage = (page: number) => {
    if (disabled || page === activePage || page < 1 || page > lastPage) return;
    onPageChange(page);
  };

  const pageButtonBase =
    "h-10 min-w-10 rounded-[10px] px-3 text-sm transition duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7c3aed] focus-visible:ring-offset-2";
  const inactivePageButton =
    "border border-[#dfe5ef] bg-white text-[#111827] hover:bg-[#f3f4f6]";
  const disabledButton =
    "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white";

  return (
    <nav
      aria-label="Table pagination"
      className={`flex flex-col gap-4 rounded-xl border border-[#e5e7eb] bg-white px-5 py-4 shadow-[0_12px_30px_rgba(15,23,42,0.08)] sm:flex-row sm:flex-wrap sm:items-center sm:justify-between ${className}`}
    >
      <p className="text-sm font-medium text-[#64748b]">
        Showing {startItem}-{endItem} of {totalItems} {itemLabel}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-2">
        <button
          type="button"
          onClick={() => goToPage(activePage - 1)}
          disabled={disabled || activePage === 1}
          aria-label="Go to previous page"
          className={`${pageButtonBase} ${disabledButton} min-w-[92px] border border-transparent bg-white text-[#7c3aed] hover:bg-[#f3f4f6]`}
        >
          Previous
        </button>

        {pageTokens.map((token) => {
          if (typeof token !== "number") {
            return (
              <span
                key={token}
                aria-hidden="true"
                className="flex h-10 min-w-10 items-center justify-center rounded-[10px] px-2 text-sm font-semibold text-[#8a8f99]"
              >
                ...
              </span>
            );
          }

          const isActive = token === activePage;

          return (
            <button
              key={token}
              type="button"
              onClick={() => goToPage(token)}
              disabled={disabled || isActive}
              aria-label={`Go to page ${token}`}
              aria-current={isActive ? "page" : undefined}
              className={`${pageButtonBase} ${disabledButton} ${
                isActive
                  ? "bg-[#7c3aed] font-semibold text-white"
                  : inactivePageButton
              }`}
            >
              {token}
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => goToPage(activePage + 1)}
          disabled={disabled || activePage === lastPage}
          aria-label="Go to next page"
          className={`${pageButtonBase} ${disabledButton} min-w-[72px] border border-transparent bg-white text-[#7c3aed] hover:bg-[#f3f4f6]`}
        >
          Next
        </button>
      </div>

      <label className="relative block w-full sm:w-auto">
        <span className="sr-only">Rows per page</span>
        <select
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
          disabled={disabled}
          aria-label="Rows per page"
          className="h-10 w-full min-w-[148px] appearance-none rounded-[10px] border border-[#aeb8d4] bg-white py-0 pl-5 pr-10 text-sm font-semibold text-[#111827] transition duration-200 ease-in-out hover:bg-[#f8fafc] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7c3aed] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
        >
          {PAGE_SIZE_OPTIONS.map((size) => (
            <option key={size} value={size}>
              {size} / page
            </option>
          ))}
        </select>
        <ChevronDown
          aria-hidden="true"
          size={18}
          className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[#111827]"
        />
      </label>
    </nav>
  );
}

export default memo(Pagination);
