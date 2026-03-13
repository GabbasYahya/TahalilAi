"use client";

const STATUS_COLORS: Record<string, string> = {
    normal: "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20",
    low: "text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20",
    high: "text-orange-700 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20",
    borderline: "text-yellow-700 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20",
};

interface Biomarker {
    marker_name: string;
    measured_value: string;
    reference_range: string;
    status: string;
    clinical_significance: string;
}

interface BiomarkerTableProps {
    biomarkers: Biomarker[];
}

export function BiomarkerTable({ biomarkers }: BiomarkerTableProps) {
    if (!biomarkers || biomarkers.length === 0) return null;

    return (
        <div className="rounded-2xl bg-white dark:bg-slate-800 ring-1 ring-slate-100 dark:ring-slate-700 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700">
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">Detailed Biomarker Analysis</h3>
            </div>

            {/* Desktop table */}
            <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                            <th className="px-6 py-3 text-left font-semibold text-slate-600 dark:text-slate-400">Marker</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-400">Value</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-400">Reference</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-400">Status</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-400">Significance</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                        {biomarkers.map((bm, i) => {
                            const statusStyle = STATUS_COLORS[bm.status] || STATUS_COLORS.normal;
                            return (
                                <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                                    <td className="px-6 py-3 font-medium text-slate-800 dark:text-slate-200">{bm.marker_name}</td>
                                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-mono text-xs">{bm.measured_value}</td>
                                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">{bm.reference_range}</td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusStyle}`}>
                                            {bm.status.charAt(0).toUpperCase() + bm.status.slice(1)}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400 text-xs max-w-xs">{bm.clinical_significance}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden divide-y divide-slate-100 dark:divide-slate-700">
                {biomarkers.map((bm, i) => {
                    const statusStyle = STATUS_COLORS[bm.status] || STATUS_COLORS.normal;
                    return (
                        <div key={i} className="px-5 py-4 space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="font-medium text-slate-800 dark:text-slate-200 text-sm">{bm.marker_name}</span>
                                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusStyle}`}>
                                    {bm.status.charAt(0).toUpperCase() + bm.status.slice(1)}
                                </span>
                            </div>
                            <div className="flex items-baseline gap-3 text-xs">
                                <span className="font-mono text-slate-700 dark:text-slate-300">{bm.measured_value}</span>
                                <span className="text-slate-400 dark:text-slate-500">Ref: {bm.reference_range}</span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">{bm.clinical_significance}</p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
