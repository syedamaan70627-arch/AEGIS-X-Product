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
    <div className="space-y-4">
      {(searchPlaceholder || actions) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          {searchPlaceholder ? (
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchValue}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </div>
          ) : (
            <div />
          )}
          {actions && <div className="flex items-center space-x-2 shrink-0">{actions}</div>}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-900/60 shadow-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono tracking-wider text-[11px] border-b border-slate-800">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={`px-4 py-3 font-semibold ${
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
                  } ${col.className || ""}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-slate-400">
                  <div className="max-w-xs mx-auto space-y-1">
                    <p className="font-semibold text-slate-300 text-sm">{emptyTitle}</p>
                    <p className="text-xs text-slate-400">{emptyDescription}</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr key={keyExtractor(row)} className="hover:bg-slate-800/40 transition-colors group">
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
                        className={`px-4 py-3 text-slate-300 ${
                          col.align === "right" ? "text-right font-mono" : col.align === "center" ? "text-center" : ""
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
