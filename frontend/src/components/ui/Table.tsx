import React from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';
import EmptyState from './EmptyState';

export interface Column<T> {
  key: string;
  header: React.ReactNode;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  className?: string;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string | number;
  isLoading?: boolean;
  emptyMessage?: string;
  emptyDescription?: string;
  emptyAction?: {
    label: string;
    onClick: () => void;
  };
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  pagination?: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    pageSize: number;
    onPageChange: (page: number) => void;
  };
  onRowClick?: (row: T) => void;
  className?: string;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyMessage = 'No records found',
  emptyDescription = 'There is currently no data matching your criteria.',
  emptyAction,
  sortBy,
  sortOrder,
  onSort,
  pagination,
  onRowClick,
  className,
}: TableProps<T>) {
  return (
    <div className={cn('w-full flex flex-col', className)}>
      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
          <thead className="bg-slate-50/80 text-xs font-semibold uppercase tracking-wider text-slate-500 border-b border-slate-200 dark:bg-slate-850 dark:border-slate-800 dark:text-slate-400">
            <tr>
              {columns.map((col) => {
                const isSorted = sortBy === col.key;
                return (
                  <th
                    key={col.key}
                    scope="col"
                    className={cn(
                      'px-5 py-3.5 select-none',
                      col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
                      col.sortable && 'cursor-pointer hover:text-slate-900 dark:hover:text-slate-100',
                      col.className
                    )}
                    onClick={() => col.sortable && onSort && onSort(col.key)}
                  >
                    <div
                      className={cn(
                        'inline-flex items-center gap-1.5',
                        col.align === 'center' && 'justify-center',
                        col.align === 'right' && 'justify-end'
                      )}
                    >
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="text-slate-400">
                          {isSorted ? (
                            sortOrder === 'asc' ? (
                              <ArrowUp className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                            ) : (
                              <ArrowDown className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3 w-3 opacity-60" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              // Skeleton rows
              Array.from({ length: 5 }).map((_, rIdx) => (
                <tr key={`skel-${rIdx}`} className="animate-pulse">
                  {columns.map((col, cIdx) => (
                    <td key={`skel-${rIdx}-${cIdx}`} className="px-5 py-4">
                      <div className="h-4 rounded bg-slate-200 dark:bg-slate-800 w-3/4" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-5 py-12">
                  <EmptyState
                    title={emptyMessage}
                    description={emptyDescription}
                    action={emptyAction}
                  />
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={keyExtractor(row, index)}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={cn(
                    'transition-colors duration-150',
                    onRowClick
                      ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/60'
                      : 'hover:bg-slate-50/50 dark:hover:bg-slate-800/30'
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'px-5 py-4 font-normal text-slate-700 dark:text-slate-200',
                        col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
                        col.className
                      )}
                    >
                      {col.render ? col.render(row, index) : (row as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {pagination && pagination.totalPages > 1 && (
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 px-2 text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {Math.min(
                (pagination.currentPage - 1) * pagination.pageSize + 1,
                pagination.totalItems
              )}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {Math.min(
                pagination.currentPage * pagination.pageSize,
                pagination.totalItems
              )}
            </span>{' '}
            of{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {pagination.totalItems}
            </span>{' '}
            results
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={pagination.currentPage <= 1}
              onClick={() => pagination.onPageChange(pagination.currentPage - 1)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              <span>Previous</span>
            </button>

            <span className="text-slate-700 dark:text-slate-300 font-medium px-1">
              Page {pagination.currentPage} of {pagination.totalPages}
            </span>

            <button
              type="button"
              disabled={pagination.currentPage >= pagination.totalPages}
              onClick={() => pagination.onPageChange(pagination.currentPage + 1)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <span>Next</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Table;
