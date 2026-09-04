"use client";

import React from "react";
import { Search } from "lucide-react";

export interface Column<T> {
  header: string;
  accessor?: keyof T | ((row: T) => React.ReactNode);
  className?: string;
  align?: "left" | "center" | "right";
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (row: T) => string;
  emptyTitle?: string;
  emptyDescription?: string;
  searchPlaceholder?: string;
  onSearchChange?: (term: string) => void;
  searchValue?: string;
  actions?: React.ReactNode;
}

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  emptyTitle = "No records found",
  emptyDescription = "There are no entries to display at this time.",
  searchPlaceholder,
  onSearchChange,
  searchValue = "",
  actions,
}: DataTableProps<T>) {
  return (
    <div className="space-y-4 font-sans">
      {(searchPlaceholder || actions) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          {searchPlaceholder ? (
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#6B7280] pointer-events-none" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchValue}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="w-full bg-[#0F141B] border border-[#26303D] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#F3F4F6] placeholder-[#6B7280] focus:outline-none focus:border-[#3B82F6] transition-all font-sans"
              />
            </div>
          ) : (
            <div />
          )}
          {actions && <div className="flex items-center space-x-2 shrink-0">{actions}</div>}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-[#26303D] bg-[#151B23] shadow-sm">
        <table className="w-full text-left text-xs border-collapse font-sans">
          <thead className="bg-[#0F141B] text-[#9CA3AF] uppercase font-sans tracking-wider text-[11px] border-b border-[#26303D]">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={`px-4 py-3.5 font-semibold ${
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
                  } ${col.className || ""}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#26303D]/60">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-[#9CA3AF]">
                  <div className="max-w-xs mx-auto space-y-1">
                    <p className="font-semibold text-[#F3F4F6] text-sm font-sans">{emptyTitle}</p>
                    <p className="text-xs text-[#9CA3AF] font-sans">{emptyDescription}</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr key={keyExtractor(row)} className="hover:bg-[#1A222C] transition-colors group">
                  {columns.map((col, colIdx) => {
                    const content =
                      typeof col.accessor === "function"
                        ? col.accessor(row)
                        : col.accessor
                        ? (row[col.accessor] as unknown as React.ReactNode)
                        : null;
                    return (
                      <td
                        key={colIdx}
                        className={`px-4 py-3.5 text-[#F3F4F6] ${
                          col.align === "right" ? "text-right font-mono tabular-nums" : col.align === "center" ? "text-center" : ""
                        } ${col.className || ""}`}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
